"""
NutriDecrypte blog-auto , Phase 2 pipeline.

Mistral large (draft) -> Claude Sonnet (audit grounding + fact-check) -> Mistral (fix).
Enriched with Gemini 2.5 Pro SERP brief (Google Search grounding).

Loads next due article from articles_plan.json, generates full markdown file, pushes to
site/src/content/blog/ via GitHub Contents API (atomic, avoids race with deploy-site push).

Runtime ~ 10 to 14 minutes per article.
"""
from __future__ import annotations

# PHASE 2 , this is a placeholder the first deploy of site will not need it.
# Real implementation will copy ~/stack-2026/petfoodrate/blog-auto/publish.py
# and adapt the brand voice + article_plan schema.

import os
import sys


def main():
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    print(f"[nutridecrypte blog-auto] dry_run={dry_run}")
    print("[nutridecrypte blog-auto] Phase 2 pipeline scaffold , no-op for now.")
    print("[nutridecrypte blog-auto] Will be wired up once Phase 1 catalogue is live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
