"""
ingest_off.py , upsert discovered Open Food Facts products into Supabase,
applying the NutriDecrypte Score (scoring_engine.compute_grade).

Usage :
    export SUPABASE_URL=https://zrgchcrhufdbreykipkj.supabase.co
    export SUPABASE_SERVICE_KEY=sb_secret_...
    python3 ingest_off.py --input ../pending/off_dietary-supplements_france.jsonl

Behaviour :
    - Read JSONL file produced by discover_off.py
    - For each product, compute 5 sub-scores + overall grade
    - Audit marketing claims via claims_auditor
    - Upsert into public.products (by barcode)
    - Upsert brand into public.brands if missing

Idempotent : reruns are safe, only changed fields are overwritten.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from scoring_engine import compute_grade, ProductInput
from claims_auditor import audit_claims

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
    "User-Agent": "nutridecrypte-ingest/0.1 (+contact@nutridecrypte.com)",
}


def slugify(text: str, max_len: int = 80) -> str:
    import re, unicodedata
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len]


def pick(product: dict, *keys: str) -> str | None:
    for k in keys:
        v = product.get(k)
        if v:
            return v
    return None


def guess_category_type(categories_tags: list[str]) -> str:
    tags = " ".join(categories_tags or []).lower()
    if "dietary-supplements" in tags or "food-supplements" in tags or "complements-alimentaires" in tags:
        return "supplement"
    if "beverages" in tags or "boissons" in tags or "waters" in tags or "sodas" in tags or "juices" in tags:
        return "beverage"
    return "food"


def supabase_upsert(table: str, rows: list[dict], on_conflict: str) -> None:
    if not rows:
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    data = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201, 204):
                print(f"  WARN upsert {table} status={resp.status}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:400]
        print(f"  ERR upsert {table} {e.code}: {body}", file=sys.stderr)


def transform(product: dict) -> tuple[dict, dict | None]:
    """Return (product_row, brand_row_or_none)."""
    barcode = product.get("code") or ""
    name = pick(product, "product_name_fr", "product_name", "product_name_en", "generic_name") or f"Produit {barcode}"
    brand = (pick(product, "brands") or "").split(",")[0].strip()
    brand_slug = slugify(brand) if brand else None

    categories_tags = product.get("categories_tags") or []
    countries_tags = product.get("countries_tags") or []
    cat_type = guess_category_type(categories_tags)

    # Compute NutriDecrypte Score
    score_input = ProductInput(
        nutri_score_letter=(pick(product, "nutriscore_grade", "nutrition_grade_fr") or "").lower() or None,
        nova_group=product.get("nova_group") if isinstance(product.get("nova_group"), int) else None,
        additives_tags=product.get("additives_tags") or [],
        labels_tags=product.get("labels_tags") or [],
        claims_flagged=audit_claims(product),
        nutriments=product.get("nutriments") or {},
        category_type=cat_type,
    )
    breakdown = compute_grade(score_input)

    slug = slugify(f"{name} {brand}".strip())[:80] or f"produit-{barcode}"

    # Shrink off_data to key fields to avoid bloating Supabase row
    off_data_compact = {
        "product_name": pick(product, "product_name_fr", "product_name", "product_name_en"),
        "brands": product.get("brands"),
        "generic_name": product.get("generic_name"),
        "nutriscore_grade": product.get("nutriscore_grade"),
        "nutriscore_score": product.get("nutriscore_score"),
        "nova_group": product.get("nova_group"),
        "categories_tags": categories_tags,
        "labels_tags": product.get("labels_tags"),
        "ingredients_text": (product.get("ingredients_text") or "")[:5000],
        "ingredients_text_fr": (product.get("ingredients_text_fr") or "")[:5000],
        "last_modified_t": product.get("last_modified_t"),
    }

    product_row = {
        "slug": slug,
        "barcode": barcode or None,
        "name": name,
        "brand_slug": brand_slug,
        "categories": categories_tags,
        "countries": countries_tags,
        "off_data": off_data_compact,
        "ingredients_text": (product.get("ingredients_text_fr") or product.get("ingredients_text") or "")[:8000],
        "nutrition_grade": pick(product, "nutriscore_grade", "nutrition_grade_fr"),
        "nova_group": product.get("nova_group") if isinstance(product.get("nova_group"), int) else None,
        "additives_tags": product.get("additives_tags") or [],
        "allergens_tags": product.get("allergens_tags") or [],
        "labels_tags": product.get("labels_tags") or [],
        "score_nutri": breakdown.nutri,
        "score_nova": breakdown.nova,
        "score_additives": breakdown.additives,
        "score_claims": breakdown.claims,
        "score_density": breakdown.density,
        "score_overall": breakdown.overall,
        "grade": breakdown.grade,
        "warnings": breakdown.warnings,
        "image_url": pick(product, "image_url", "image_front_small_url"),
        "image_small_url": pick(product, "image_small_url", "image_front_small_url"),
        "last_scored_at": "now()",
    }

    brand_row = None
    if brand_slug:
        brand_row = {
            "slug": brand_slug,
            "name": brand,
        }

    return product_row, brand_row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSONL file from discover_off.py")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=0, help="Process first N products only (0 = all)")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("FATAL: SUPABASE_URL and SUPABASE_SERVICE_KEY env vars required", file=sys.stderr)
        sys.exit(1)

    path = Path(args.input)
    if not path.exists():
        print(f"FATAL: input file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # Two-pass : first collect brands + deduped products, then upsert brands first
    products_by_slug: dict[str, dict] = {}
    brands_seen: dict[str, dict] = {}
    total_seen = 0
    t0 = time.time()

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                off = json.loads(line)
            except json.JSONDecodeError:
                continue

            p_row, b_row = transform(off)
            # dedup : keep the most recently seen version of a product slug
            products_by_slug[p_row["slug"]] = p_row
            if b_row and b_row["slug"] not in brands_seen:
                brands_seen[b_row["slug"]] = b_row

            total_seen += 1
            if args.limit and total_seen >= args.limit:
                break

    # 1. upsert brands FIRST (FK target)
    if brands_seen:
        brands_list = list(brands_seen.values())
        for i in range(0, len(brands_list), 100):
            supabase_upsert("brands", brands_list[i:i+100], "slug")
        print(f"  {len(brands_seen)} brands upserted ({time.time()-t0:.1f}s)")

    # 2. upsert products in batches (deduped)
    products_list = list(products_by_slug.values())
    for i in range(0, len(products_list), args.batch_size):
        supabase_upsert("products", products_list[i:i+args.batch_size], "slug")
    print(f"  {len(products_list)} products upserted (from {total_seen} raw rows)")

    print(f"DONE in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
