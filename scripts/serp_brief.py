"""Enrichit articles.json avec un brief SERP par article, via Gemini 2.5 Pro + Google Search grounding.

Pour chaque keyword cible, Gemini 2.5 Pro :
  1. Execute une recherche Google.fr groundee (native grounding tool)
  2. Analyse le top 10 concurrents
  3. Retourne un brief JSON structure : angles couverts, angles faibles, winning moves, sections obligatoires, faits citables, intent type

Le brief est stocke dans articles.json[*].serp_brief et consomme par publish.py.

Usage:
  python3 scripts/serp_brief.py                 # tous articles non-enrichis
  python3 scripts/serp_brief.py --force         # re-enrichit tout
  python3 scripts/serp_brief.py --index 0       # un seul article
  python3 scripts/serp_brief.py --max 3         # limite a 3 articles

Env requis (dans ~/stack-2026/.env.master):
  GOOGLE_API_KEY      Gemini API key (projet avec Generative Language API + billing)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_MASTER = Path.home() / "stack-2026" / ".env.master"
if ENV_MASTER.exists():
    load_dotenv(ENV_MASTER)
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
ARTICLES_FILE = REPO_DIR / "blog-auto" / "articles.json"

GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("serp_brief")


BRIEF_PROMPT_TEMPLATE = """Tu es un strategiste SEO et GEO (Generative Engine Optimization) specialise en niche : pet food, ingredient analysis, brand comparison (cat, dog, bird, rabbit, etc.).

Execute une recherche Google.com pour la requete ci-dessous. Lis attentivement les 10 premiers resultats. Identifie ce qui ranke, les angles communs, les angles faibles, et ce qu'il faut faire pour battre le top 3.

REQUETE : "{keyword}"
MARCHE CIBLE : EN international + FR, pet owners researching food quality and brand transparency
NOTRE POSITIONNEMENT : PetFoodRate, the Nutri-Score for pet food, A-E grading on 5 criteria (ingredients, nutrition, safety, transparency, fit)

Retourne UNIQUEMENT ce JSON strict (aucun texte autour, pas de bloc markdown, pas de commentaire) :

{{
  "top10": [
    {{"rank": 1, "domain": "...", "title": "...", "main_angle": "une phrase qui resume l'angle edito", "strength": "point fort observe", "weakness": "limite observee"}}
  ],
  "common_angles": ["angle couvert par la plupart des concurrents 1", "angle 2", "angle 3"],
  "weak_angles": ["angle mal traite ou absent 1", "angle 2", "angle 3"],
  "winning_moves": [
    "move 1 precis et actionnable pour battre le top 3",
    "move 2 precis",
    "move 3 precis",
    "move 4 precis",
    "move 5 precis"
  ],
  "must_include_sections": [
    "titre H2 precis a inclure pour couvrir l'intention",
    "titre H2 2",
    "titre H2 3",
    "titre H2 4",
    "titre H2 5",
    "titre H2 6"
  ],
  "citable_facts_to_verify": [
    "stat/chiffre que les concurrents citent (source a verifier) 1",
    "fait precis 2",
    "fait precis 3"
  ],
  "entities_to_mention": ["nom entite 1 (marque, organisme, etude)", "entite 2", "entite 3"],
  "target_word_count": 3000,
  "intent_type": "informational",
  "featured_snippet_opportunity": "format du snippet a viser (definition, liste, tableau, steps) + formulation cible",
  "serp_features_detected": ["AI Overview", "People Also Ask", "Featured Snippet", "Video", "Image Pack"]
}}

Regles pour le JSON :
- JSON strict, champs tous remplis (meme vides : [] ou \"\")
- Response language: match REQUETE language (EN or FR)
- Prise en compte des SERP features visibles (AI Overview, PAA, etc.)
- Orientation GEO : pense LLM citability (ChatGPT, Perplexity, AI Overviews)"""


def gemini_serp_brief(keyword: str, retries: int = 3) -> dict:
    """Call Gemini 2.5 Pro with Google Search grounding and parse JSON brief."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY manquant (cf ~/stack-2026/.env.master)")

    payload = {
        "contents": [{"parts": [{"text": BRIEF_PROMPT_TEMPLATE.format(keyword=keyword)}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4000,
        },
    }

    last_err = None
    for attempt in range(retries):
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GOOGLE_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=180,
            )
            if r.status_code in (429, 500, 502, 503):
                wait = 10 * (2 ** attempt)
                log.warning(f"Gemini HTTP {r.status_code}, retry {attempt + 1}/{retries} dans {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            cand = (data.get("candidates") or [{}])[0]
            parts = cand.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if "text" in p)
            # Find JSON in response
            # Strip markdown fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text.strip())
            text = re.sub(r"\s*```$", "", text)
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                raise ValueError("no JSON in Gemini response")
            brief = json.loads(m.group())
            # Attach grounding sources
            grounding = cand.get("groundingMetadata", {})
            chunks = grounding.get("groundingChunks", [])
            brief["grounding_sources"] = [
                {"title": c.get("web", {}).get("title", ""), "uri": c.get("web", {}).get("uri", "")}
                for c in chunks[:15]
            ]
            return brief
        except Exception as e:
            last_err = e
            log.warning(f"Gemini attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"Gemini SERP brief failed after {retries} attempts: {last_err}")


def enrich_article(article: dict) -> dict:
    keyword = (article.get("keywords") or article["title"]).split(",")[0].strip()
    log.info(f"[{article.get('index','?')}] Keyword: {keyword}")
    brief = gemini_serp_brief(keyword)
    top10 = brief.get("top10", [])
    log.info(f"  Top {len(top10)} analyses, {len(brief.get('winning_moves', []))} winning moves")
    return {
        "keyword": keyword,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": GEMINI_MODEL,
        "brief": brief,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--index", type=int)
    ap.add_argument("--max", type=int, default=999)
    args = ap.parse_args()

    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    targets = []
    for a in articles:
        if args.index is not None and a.get("index") != args.index:
            continue
        if not args.force and a.get("serp_brief"):
            continue
        if a.get("published"):
            continue
        targets.append(a)
    targets = targets[: args.max]

    log.info(f"{len(targets)} articles a enrichir via Gemini 2.5 Pro + Google Search grounding")
    for a in targets:
        try:
            a["serp_brief"] = enrich_article(a)
            # Save incrementally to avoid losing progress on crash
            ARTICLES_FILE.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            time.sleep(2)  # gentle pacing
        except Exception as e:
            log.error(f"[{a.get('index','?')}] {e}")
            continue

    log.info(f"articles.json mis a jour ({ARTICLES_FILE})")


if __name__ == "__main__":
    main()
