#!/usr/bin/env python3
"""
NutriDecrypte blog auto-publisher.

Reads `articles_plan.json`, finds the next article whose `scheduled_date` is <= today
and whose markdown file does not yet exist in site/src/content/blog/.

Pipeline:
  1. Optional SERP brief enrichment via Gemini (if GOOGLE_API_KEY present)
  2. Mistral large draft
  3. Claude Sonnet audit (grounded fact-check)
  4. Mistral fix pass
  5. Write Markdown with frontmatter to site/src/content/blog/<slug>.md
  6. Push via GitHub Contents API (atomic, no race)

Runs daily via GitHub Actions cron, target 07:00 to 09:00 Europe/Paris.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
import re
import sys
import time
from datetime import datetime, date, timezone
from pathlib import Path

import requests

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
try:
    from mistral_pipeline import generate_with_mistral_audit
except Exception as e:
    print(f"[warn] mistral_pipeline not importable: {e}")
    generate_with_mistral_audit = None

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
try:
    from serp_brief import enrich_article_with_serp_brief  # optional
except Exception:
    enrich_article_with_serp_brief = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nutridecrypte-blog-auto")

# ============================================================
# Paths
# ============================================================
BLOG_AUTO_DIR = Path(__file__).parent
PLAN_FILE = BLOG_AUTO_DIR / "articles_plan.json"
PROMPT_FILE = BLOG_AUTO_DIR / "prompts" / "article-seo.md"
BLOG_DIR = BLOG_AUTO_DIR.parent / "site" / "src" / "content" / "blog"
LOG_DIR = BLOG_AUTO_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================
# Config / brand
# ============================================================
SITE_NAME = "NutriDecrypte"
SITE_URL = "https://nutridecrypte.com"
APP_URL = "https://nutridecrypte.com"
SITE_DESCRIPTION = "Decodeur d'etiquettes alimentaires independant, grades A a E sur Nutri-Score + NOVA + additifs + allegations + densite."
POSITIONING = "Decodeur francais d'etiquettes et d'additifs, independant des industriels"

AUTHORS = ["Camille Roux", "Thomas Moreau", "Sarah Keller", "Lucie Bernard"]

FORBIDDEN_PHRASES = "jargon marketing creux, formulations corporate, 'nous sommes fiers de', 'solution innovante', 'revolutionnaire'"

# GitHub push config
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO = os.environ.get("GITHUB_REPOSITORY", "STACK-2026/nutridecrypte")


# ============================================================
# Helpers
# ============================================================
def pick_author(slug: str, override: str | None = None) -> str:
    if override:
        return override
    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)
    return AUTHORS[h % len(AUTHORS)]


def today_str() -> str:
    return date.today().isoformat()


def random_publish_time_iso() -> str:
    # Randomise minute and second inside today's run window to look authentic
    now = datetime.now(timezone.utc)
    hour = random.randint(5, 7)  # UTC, maps to 07-09 Paris summer
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return now.replace(hour=hour, minute=minute, second=second, microsecond=0).isoformat()


def strip_em_dashes(text: str) -> str:
    return text.replace("—", ",").replace("–", "-")


def slug_to_path(slug: str) -> Path:
    return BLOG_DIR / f"{slug}.md"


# ============================================================
# Plan loading
# ============================================================
def load_plan() -> dict:
    with PLAN_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_next_due_article(plan: dict) -> dict | None:
    """Return first article with scheduled_date <= today whose file does not exist yet."""
    today = today_str()
    for article in plan.get("articles", []):
        sched = article.get("scheduled_date") or article.get("date")
        if not sched or sched > today:
            continue
        file_path = slug_to_path(article["slug"])
        if file_path.exists():
            continue
        return article
    return None


# ============================================================
# Prompt building
# ============================================================
def load_system_prompt() -> str:
    raw = PROMPT_FILE.read_text(encoding="utf-8")
    return (raw
            .replace("{{SITE_NAME}}", SITE_NAME)
            .replace("{{SITE_URL}}", SITE_URL)
            .replace("{{APP_URL}}", APP_URL)
            .replace("{{SITE_DESCRIPTION}}", SITE_DESCRIPTION)
            .replace("{{POSITIONING}}", POSITIONING)
            .replace("{{FORBIDDEN_PHRASES}}", FORBIDDEN_PHRASES))


def build_user_prompt(article: dict) -> str:
    lang = article.get("lang", "fr")
    title = article.get("working_title", "")
    keyword = article.get("target_keyword", "")
    angle = article.get("angle", "")

    parts = [
        f"LANG: {lang}",
        f"KEYWORD PRINCIPAL: {keyword}",
        f"TITRE DE TRAVAIL: {title}",
        f"ANGLE EDITORIAL: {angle}",
        "",
        "Genere un article complet respectant les standards STACK-2026 (3500+ mots, TL;DR, FAQ, Sources 5+, 10+ liens internes, 5+ liens externes autorite, zero tiret cadratin).",
        "",
        "Les liens internes doivent pointer vers des pages de nutridecrypte.com :",
        "- /methodology (algorithme de notation)",
        "- /encyclopedia (base des additifs)",
        "- /rankings (classements produits)",
        "- /blog/<autre-article> (si pertinent)",
        "",
        "Les liens externes doivent pointer vers autorites francaises/europeennes : ANSES (anses.fr), EFSA (efsa.europa.eu), INSERM (inserm.fr), Sante Publique France (santepubliquefrance.fr), Open Food Facts (openfoodfacts.org), OMS (who.int).",
    ]

    # SERP brief enrichment
    serp = article.get("serp_brief") or {}
    if serp:
        parts.append("\n=== BRIEF CONCURRENTIEL SERP ===")
        parts.append(json.dumps(serp, ensure_ascii=False, indent=2)[:4000])
        parts.append("=== FIN BRIEF ===")
        parts.append("Exploite ces angles faibles et winning moves pour ecraser le top 3 Google par design.")

    return "\n".join(parts)


# ============================================================
# Output parsing
# ============================================================
def extract_frontmatter_fields(generated: str) -> tuple[str, str, str]:
    """Extract TITLE_TAG, META_DESCRIPTION, body from LLM output."""
    title_match = re.search(r"^TITLE_TAG:\s*(.+)$", generated, re.MULTILINE)
    meta_match = re.search(r"^META_DESCRIPTION:\s*(.+)$", generated, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    meta = meta_match.group(1).strip() if meta_match else ""

    # Strip the header lines from body
    body = generated
    if title_match:
        body = re.sub(r"^TITLE_TAG:\s*.+\n?", "", body, count=1, flags=re.MULTILINE)
    if meta_match:
        body = re.sub(r"^META_DESCRIPTION:\s*.+\n?", "", body, count=1, flags=re.MULTILINE)

    # Clean leading whitespace and stray code fences
    body = body.strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-z]*\n?", "", body)
        body = re.sub(r"\n?```$", "", body)

    return title, meta, body.strip()


def build_markdown_file(article: dict, title: str, meta: str, body: str, author: str) -> str:
    slug = article["slug"]
    lang = article.get("lang", "fr")
    category = article.get("category", "guide")
    keywords = article.get("target_keyword", "")
    image_url = article.get("image_url") or "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1200&q=80"
    image_alt = f"Illustration {title[:80]}"

    # Sanitize body from em-dashes
    body = strip_em_dashes(body)
    title = strip_em_dashes(title)
    meta = strip_em_dashes(meta)

    pub_iso = random_publish_time_iso()
    last_reviewed = today_str()

    fm = [
        "---",
        f'title: {json.dumps(title, ensure_ascii=False)}',
        f'description: {json.dumps(meta[:160], ensure_ascii=False)}',
        f'date: {pub_iso}',
        f'lastReviewed: {last_reviewed}',
        f'author: {json.dumps(author, ensure_ascii=False)}',
        f'reviewedBy: "NutriDecrypte Editorial"',
        f'category: {json.dumps(category, ensure_ascii=False)}',
        f'tags: {json.dumps([keywords] if keywords else [], ensure_ascii=False)}',
        f'image: {json.dumps(image_url, ensure_ascii=False)}',
        f'imageAlt: {json.dumps(image_alt, ensure_ascii=False)}',
        f'lang: {lang}',
        f'keywords: {json.dumps(keywords, ensure_ascii=False)}',
        f'draft: false',
        "---",
        "",
        body,
        "",
    ]
    return "\n".join(fm)


# ============================================================
# GitHub Contents API push
# ============================================================
def push_via_github_api(rel_path: str, content: str, message: str) -> bool:
    """Put file via https://api.github.com/repos/:owner/:repo/contents/:path. Atomic.
    If file already exists, includes SHA for update, but for blog-auto it should be create-only.
    """
    if not GH_TOKEN:
        log.warning("GITHUB_TOKEN absent, skip push (dry run)")
        return False

    url = f"https://api.github.com/repos/{GH_REPO}/contents/{rel_path}"
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {
        "message": message,
        "content": encoded,
        "branch": "main",
        "committer": {"name": "nutridecrypte-blog-auto[bot]", "email": "blog-auto@users.noreply.github.com"},
    }

    # If file exists (race with manual edit), get SHA first
    head = requests.get(url, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    }, params={"ref": "main"}, timeout=30)
    if head.status_code == 200:
        payload["sha"] = head.json().get("sha", "")

    resp = requests.put(url, json=payload, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }, timeout=60)

    if resp.status_code in (200, 201):
        commit = resp.json().get("commit", {}).get("sha", "")[:8]
        log.info(f"Pushed {rel_path} via GitHub API (sha {commit})")
        return True
    log.error(f"Push failed {resp.status_code}: {resp.text[:300]}")
    return False


def update_plan_in_github(plan: dict) -> bool:
    """Upsert articles_plan.json with updated published flag."""
    if not GH_TOKEN:
        return False
    rel_path = "blog-auto/articles_plan.json"
    new_content = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    return push_via_github_api(rel_path, new_content, f"chore(blog-auto): mark {plan.get('last_published','?')} as published")


# ============================================================
# Main
# ============================================================
def main() -> int:
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    log.info(f"start , dry_run={dry_run}")

    plan = load_plan()
    article = find_next_due_article(plan)
    if not article:
        log.info("No article due today. Bye.")
        return 0

    slug = article["slug"]
    lang = article.get("lang", "fr")
    log.info(f"next article: {slug} ({lang}) - {article.get('working_title','')}")

    # 0) Optional SERP brief enrichment
    if enrich_article_with_serp_brief and os.environ.get("GOOGLE_API_KEY"):
        try:
            article = enrich_article_with_serp_brief(article)
            log.info("serp_brief enriched")
        except Exception as e:
            log.warning(f"serp_brief failed: {e}")

    # 1) Build prompts
    system_prompt = load_system_prompt()
    user_prompt = build_user_prompt(article)

    if dry_run:
        log.info("DRY RUN , not calling LLM. Prompt lengths: system=%d user=%d", len(system_prompt), len(user_prompt))
        log.info(f"Would write {slug}.md")
        return 0

    if not generate_with_mistral_audit:
        log.error("mistral_pipeline not available, abort")
        return 1
    if not os.environ.get("MISTRAL_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("MISTRAL_API_KEY + ANTHROPIC_API_KEY required, abort")
        return 1

    # 2) Generate (Mistral draft -> Claude audit -> Mistral fix)
    t0 = time.time()
    try:
        generated = generate_with_mistral_audit(system_prompt, user_prompt)
    except Exception as e:
        log.error(f"generation failed: {e}")
        return 1
    elapsed = time.time() - t0
    log.info(f"generated in {elapsed:.1f}s , {len(generated)} chars")

    # 3) Parse output
    title, meta, body = extract_frontmatter_fields(generated)
    if not title or not body:
        log.error("could not extract TITLE_TAG or body from generated content")
        (LOG_DIR / f"{slug}.raw.md").write_text(generated, encoding="utf-8")
        return 1

    author = pick_author(slug, article.get("author_pen_name"))

    # 4) Build final markdown
    final = build_markdown_file(article, title, meta, body, author)

    # 5) Push via GitHub API
    rel_path = f"site/src/content/blog/{slug}.md"
    commit_msg = f"blog-auto: publish {slug} ({lang})"
    pushed = push_via_github_api(rel_path, final, commit_msg)

    if not pushed:
        # local fallback
        p = slug_to_path(slug)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(final, encoding="utf-8")
        log.warning(f"wrote locally to {p} (push failed)")

    log.info(f"DONE {slug} in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
