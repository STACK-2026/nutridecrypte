#!/usr/bin/env python3
"""
Mistral+Claude-audit pipeline for blog article generation — STACK-2026 quality standards.

Targets:
  - 3500+ words body
  - TL;DR block at top
  - FAQ section with 5+ questions
  - Sources section with 5+ verified refs
  - 10+ internal links, 5+ external authority links
  - E-E-A-T signals
  - No em/en dashes

Usage in publish.py:
    # Add to imports (same dir as mistral_pipeline.py)
    sys.path.insert(0, str(Path(__file__).parent))
    from mistral_pipeline import generate_with_mistral_audit

    # Dispatch based on secret presence
    if os.environ.get("MISTRAL_API_KEY"):
        draft = generate_with_mistral_audit(system_prompt, user_prompt)
    else:
        # legacy Claude direct
        ...

Env vars required:
  MISTRAL_API_KEY     required
  ANTHROPIC_API_KEY   required for audit step (default enabled)
"""

import json
import logging
import os
import re
import time

import requests

log = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

MISTRAL_LARGE = "mistral-large-latest"
MISTRAL_SMALL = "mistral-small-latest"
CLAUDE_SONNET = "claude-sonnet-4-6"

API_TIMEOUT = 300


DRAFT_SUFFIX = """

STANDARDS QUALITE OBLIGATOIRES STACK-2026 (article rejete si non respectes):
- LONGUEUR : 3500+ mots dans le corps (hors frontmatter).
- TL;DR : bloc "**TL;DR**" au debut (avant 1ere H2) avec 3-5 bullets.
- STRUCTURE : intro 200-300 mots, minimum 6 sections H2, sous-sections H3.
- FAQ : section "## FAQ" a la fin avec 5 questions + reponses 80-150 mots.
- SOURCES : section "## Sources" avec 5+ references markdown vers autorites reelles.
- MAILLAGE EXTERNE : 5+ liens [...](https://...) vers autorites (.gov, .edu, journaux, leaders reels).
- MAILLAGE INTERNE : 10+ liens [...](/...) relatifs.
- JAMAIS de tiret cadratin (em) ni en dash. Virgule/deux-points/tiret simple (-).
- Chiffres precis UNIQUEMENT si source adjacente. Sinon reformule en tendance.
- Interdit "les etudes montrent" sans source.
- Sortie STRICTEMENT Markdown, sans triple-backticks.
- E-E-A-T : expertise avec exemples concrets, cas clients, chiffres sources.
"""


AUDIT_SYSTEM = """Tu es auditeur QUALITE SEO pour standards STACK-2026. Audite le DRAFT.

SEUILS DURS (MAJOR si non respectes):
1. LONGUEUR corps : 3500+ mots. MINOR si 3000-3499, MAJOR si < 3000.
2. TL;DR : bloc "**TL;DR**" present avant 1ere H2.
3. FAQ : "## FAQ" avec au moins 5 questions.
4. SOURCES : "## Sources" avec au moins 5 references markdown.
5. LIENS EXTERNES : minimum 5 liens vers domaines differents du site courant.
6. LIENS INTERNES : minimum 10 liens [...](/...) relatifs.
7. HALLUCINATIONS : chiffres sans source, citations sans attribution, noms/lois inventes.
8. TIRETS : em dash (U+2014) ou en dash (U+2013) = MAJOR.

Retourne UNIQUEMENT ce JSON :
{
  "word_count_body": 0,
  "has_tldr": false,
  "has_faq": false,
  "faq_questions_count": 0,
  "has_sources": false,
  "sources_count": 0,
  "external_links_count": 0,
  "internal_links_count": 0,
  "em_dashes_present": false,
  "hallucinations": [{"claim": "max 180 chars", "type": "chiffre|citation|nom|date|loi", "reason": "..."}],
  "issues": [{"field": "word_count|tldr|faq|sources|external_links|internal_links|hallucinations|dashes", "severity": "MINOR|MAJOR", "description": "..."}],
  "verdict": "CLEAN|MINOR|MAJOR"
}

VERDICT :
- CLEAN = 0 issue.
- MINOR = 1-3 issues non critiques.
- MAJOR = 1+ critique : pas FAQ/Sources/TL;DR, mots<3000, hallucination grave, em-dash, liens < minima.

IGNORE: opinions, style, choix editoriaux."""


def mistral_call(messages, model=MISTRAL_LARGE, temperature=0.4, max_tokens=14000,
                 json_mode=False, retries=3):
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY missing")
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(MISTRAL_URL, json=payload, headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            }, timeout=API_TIMEOUT)
            if r.status_code in (429, 503):
                wait = 5 * (2 ** attempt)
                log.warning(f"Mistral {r.status_code}, retry {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            log.warning(f"Mistral error attempt {attempt + 1}: {e}")
            time.sleep(3)
    raise last or RuntimeError("Mistral failed")


def claude_audit_call(system, user, max_tokens=2500, retries=3):
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing for audit")
    payload = {"model": CLAUDE_SONNET, "max_tokens": max_tokens, "system": system,
               "messages": [{"role": "user", "content": user}]}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(ANTHROPIC_URL, json=payload, headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }, timeout=API_TIMEOUT)
            if r.status_code in (429, 529):
                wait = 10 * (2 ** attempt)
                log.warning(f"Claude {r.status_code}, retry {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            j = r.json()
            return "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
        except Exception as e:
            last = e
            log.warning(f"Claude error attempt {attempt + 1}: {e}")
            time.sleep(5)
    raise last or RuntimeError("Claude audit failed")


def _strip_md_fence(text):
    t = text.strip()
    t = re.sub(r"^```(?:markdown|md|yaml)?\s*\n", "", t)
    t = re.sub(r"\n```\s*$", "", t)
    return t.strip()


def _audit_draft(draft):
    user = f"DRAFT A AUDITER :\n\n{draft[:12000]}\n\nRetourne le JSON d'audit uniquement."
    try:
        content = claude_audit_call(AUDIT_SYSTEM, user, max_tokens=2500)
    except Exception as e:
        log.warning(f"Audit call failed: {e}")
        return {"verdict": "UNKNOWN", "issues": [], "hallucinations": []}
    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        return {"verdict": "UNKNOWN", "issues": [], "hallucinations": []}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return {"verdict": "UNKNOWN", "issues": [], "hallucinations": []}


def _fix_issues(draft, audit):
    issues = list(audit.get("issues", [])) + [
        {"field": "hallucination", "severity": "MAJOR",
         "description": f"Claim: {h.get('claim','')[:150]} | {h.get('reason','')}"}
        for h in audit.get("hallucinations", [])
    ]
    if not issues:
        return draft
    issues_text = "\n".join(
        f"- [{i.get('severity','?')}] {i.get('field','?')}: {i.get('description','')}"
        for i in issues[:25]
    )
    wc = audit.get("word_count_body", 0)
    user = f"""Auditeur a flagge {len(issues)} problemes. Corrige en developpant intelligemment.

PROBLEMES :
{issues_text}

Longueur actuelle : {wc} mots.

DIRECTIVES :
- Si word_count < 3500 : DEVELOPPE les sections existantes avec exemples, chiffres sources, nuances. Ajoute H2/H3 supplementaires. Atteins 3500+ mots.
- Si TL;DR absent : ajoute "**TL;DR**" + 3-5 bullets au tout debut avant la 1ere H2.
- Si FAQ absente/<5 questions : ajoute/etend "## FAQ" avec 5 questions + reponses 80-150 mots.
- Si Sources absente/<5 refs : ajoute/etend "## Sources" avec liens reels.
- Si liens externes < 5 : injecte vers autorites reelles (.gov, journaux, leaders secteur).
- Si liens internes < 10 : injecte vers /blog/..., /tarifs, /outils, /methode.
- Si em/en dash : remplace TOUS.
- Si hallucinations : retire ou reformule en tendance.

Conserve frontmatter (TITLE_TAG, META_DESCRIPTION) INTACT. Garde structure/style. Modifie UNIQUEMENT flagge.

DRAFT :
{draft}

Retourne draft corrige COMPLET, sans commentaire, sans triple-backticks."""
    return mistral_call(
        [{"role": "system", "content": "Corrige les issues en developpant pour atteindre standards STACK-2026."},
         {"role": "user", "content": user}],
        model=MISTRAL_LARGE, temperature=0.25, max_tokens=14000,
    )


def generate_with_mistral_audit(system_prompt, user_prompt,
                                max_tokens=14000, temperature=0.4,
                                do_audit=True):
    """
    Core pipeline: Mistral-large draft → Claude audit → Mistral fix.

    Returns: article text (includes TITLE_TAG/META_DESCRIPTION lines + body).
    """
    log.info("[1/3] Mistral-large drafting...")
    draft = mistral_call(
        [{"role": "system", "content": system_prompt + DRAFT_SUFFIX},
         {"role": "user", "content": user_prompt}],
        model=MISTRAL_LARGE, temperature=temperature, max_tokens=max_tokens,
    )
    draft = _strip_md_fence(draft)

    if not do_audit or not ANTHROPIC_API_KEY:
        log.info("  Audit skipped (no audit or no ANTHROPIC_API_KEY)")
        return draft

    log.info("[2/3] Claude audit...")
    audit = _audit_draft(draft)
    verdict = audit.get("verdict", "UNKNOWN")
    issues = audit.get("issues", [])
    halls = audit.get("hallucinations", [])
    wc = audit.get("word_count_body", 0)
    log.info(f"  verdict={verdict} mots={wc} issues={len(issues)} hallucinations={len(halls)}")

    if verdict == "MAJOR" or (issues and len(issues) >= 2):
        log.info("[3/3] Mistral-large fix issues...")
        fixed = _fix_issues(draft, audit)
        fixed = _strip_md_fence(fixed)
        return fixed
    elif verdict == "MINOR":
        log.info(f"  MINOR issues kept (not worth re-running):")
        for i in issues[:3]:
            log.info(f"    - {i.get('field')}: {i.get('description', '')[:80]}")

    return draft
