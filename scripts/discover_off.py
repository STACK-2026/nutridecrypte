"""
discover_off.py , discover products from Open Food Facts by category.

Usage:
    python3 discover_off.py --category dietary-supplements --country france --limit 500
    python3 discover_off.py --category breakfast-cereals  --country france --limit 1000
    python3 discover_off.py --category yogurts            --country france --limit 1000

Output: writes JSONL to ../pending/off_<category>_<country>.jsonl

Later ingested by scripts/ingest_off.py which applies scoring_engine.compute_grade
and upserts into Supabase public.products.

Notes:
    - Open Food Facts is CC-BY-SA 4.0, attribution and same-license required.
    - Always pass a real User-Agent , OFF rate-limits anonymous scrapers.
    - We paginate through the v2 search API, not the v1 category JSON (more stable).
"""

from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

USER_AGENT = "nutridecrypte/0.1 (contact@nutridecrypte.com)"

FIELDS = [
    "code",
    "product_name",
    "product_name_fr",
    "product_name_en",
    "generic_name",
    "brands",
    "brands_tags",
    "categories_tags",
    "countries_tags",
    "labels_tags",
    "ingredients_text",
    "ingredients_text_fr",
    "ingredients_text_en",
    "additives_tags",
    "allergens_tags",
    "nova_group",
    "nutrition_grade_fr",
    "nutriscore_grade",
    "nutriscore_score",
    "nutriments",
    "image_url",
    "image_small_url",
    "image_front_small_url",
    "last_modified_t",
]


def fetch_page(category: str, country: str, page: int, page_size: int) -> list[dict]:
    params = {
        "categories_tags_en": category,
        "countries_tags_en": country,
        "page": page,
        "page_size": page_size,
        "fields": ",".join(FIELDS),
    }
    url = "https://world.openfoodfacts.org/api/v2/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data.get("products", []) or []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, help="OFF English category tag, e.g. dietary-supplements")
    parser.add_argument("--country", default="france", help="Country tag, default france")
    parser.add_argument("--limit", type=int, default=500, help="Max products to fetch")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--out-dir", default=str(Path(__file__).parent.parent / "pending"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"off_{args.category}_{args.country}.jsonl"

    fetched = 0
    seen = set()
    with out_file.open("w", encoding="utf-8") as f:
        page = 1
        while fetched < args.limit:
            try:
                products = fetch_page(args.category, args.country, page, args.page_size)
            except Exception as e:
                print(f"[page {page}] ERROR: {e}", file=sys.stderr)
                time.sleep(5)
                page += 1
                continue

            if not products:
                print(f"[page {page}] empty, stopping.")
                break

            new_count = 0
            for p in products:
                code = p.get("code")
                if not code or code in seen:
                    continue
                seen.add(code)
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
                fetched += 1
                new_count += 1
                if fetched >= args.limit:
                    break

            print(f"[page {page}] {new_count} new, total {fetched}/{args.limit}")
            page += 1
            time.sleep(1.5)  # polite rate limit

    print(f"DONE -> {out_file} ({fetched} products)")


if __name__ == "__main__":
    main()
