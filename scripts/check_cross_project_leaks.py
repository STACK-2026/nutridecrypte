#!/usr/bin/env python3
"""Guardrail , scan the repo for cross-project data leaks.

Fails (exit 1) when it finds:
  , a Supabase project ref that is not the one pinned for this project
  , a Cloudflare Pages project name belonging to another STACK-2026 site
  , hardcoded analytics or tracker constants from a sibling project
  , a site domain from another STACK-2026 project in runtime code

Why : on 2026-04-23 we discovered that public/tracker.js and
src/components/Analytics.astro had been copy-pasted from PetFoodRate and from
another unknown Supabase project, shipping BébéDécrypte visitor data to those
sibling databases for a full day.
Never again. This check must run on every CI push.

Config lives at the top of this file (SELF_PROJECT) so it is
obvious when this script is forked to another repo.

Usage:
  python3 scripts/check_cross_project_leaks.py
  python3 scripts/check_cross_project_leaks.py --fix        # delete offending files if safe
  python3 scripts/check_cross_project_leaks.py --json       # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pinned identity , update when the project ref / domain changes.
#
# A STACK-2026 repo can legitimately reference MORE than its single primary
# Supabase project :
#   , a split site + app (marketing site Supabase + Lovable app Supabase)
#   , a legitimate cross-project easter egg or portfolio link
# So SELF_PROJECT carries three allow-lists :
#   , `own_tokens` : brand strings the scanner must not flag
#   , `own_domains` : domain suffixes the scanner must not flag
#   , `own_supabase_refs` : Supabase project refs the scanner must not flag
# ---------------------------------------------------------------------------
SELF_PROJECT = {
    "name": 'nutridecrypte',
    "supabase_ref": 'zrgchcrhufdbreykipkj',
    "domain": 'nutridecrypte.com',
    "cf_pages_project": 'nutridecrypte',
    "own_tokens": {'NutriDecrypte', 'NutriDécrypte', 'nutridecrypte', 'nutridecrypte.com'},
    "own_domains": {'nutridecrypte.com'},
    "own_supabase_refs": {'zrgchcrhufdbreykipkj'},
}

# Known sibling STACK-2026 Supabase refs. Anything in this map that is not
# the current SELF_PROJECT ref is an automatic fail in runtime code.
# Mapping audited and cross-referenced 2026-04-23. When a new project joins
# STACK-2026, add its ref here and re-propagate this file to every repo.
KNOWN_SIBLING_SUPABASE_REFS = {
    "feqdpvahksbamwutazkl": "bebedecrypte",
    "bhmmidfnovtkcxljjfpd": "petfoodrate",
    "rxdcejlofnhjicupzikx": "econono",
    "clxawcqusiclyjzhczph": "decryptebot",
    "afvtxiklivnmakqixkml": "scoreimmo",
    "nkjbmbdrvejemzrggxvr": "karmastro",
    "commbksqnwhpsyenjzuf": "adapte-toi",
    "iihjnnytqdkdyzvohwhn": "dentalimplantquote",
    "ovptmntzrrrjxstzzceu": "getskinscore",
    "zrgchcrhufdbreykipkj": "nutridecrypte",
    "wnulejloqvyroskknljb": "pulsari",
    "ctdduvzobmjtcfsmorjr": "ukheatpumpguide",
    "eikxsaktrbuowetvymsn": "ratingcafe",
    "apuyeakgxjgdcfssrtek": "lobservatoiredespros",
    # App splits (separate Supabase for Lovable-hosted product apps, same owner)
    "gfhloroqncrfzahkaihn": "petfoodrate-app",
}

KNOWN_SIBLING_DOMAINS = {
    "bebedecrypte.com": "BébéDécrypte",
    "petfoodrate.com": "PetFoodRate",
    "econono.com": "Econono",
    "decryptebot.com": "DecrypteBot",
    "score-immo.fr": "ScoreImmo",
    "karmastro.com": "Karmastro",
    "expert-menuiserie.fr": "Expert Menuiserie",
    "litiere-agglomerante.com": "Litière Agglomérante",
    "litiereagglomerante.com": "Litière Agglomérante (alias)",
    "orthoptimal.fr": "Orthoptimal",
    "minedeteint.com": "Mine de Teint",
    "adapte-toi.com": "Adapte-toi",
    "dentalimplantquote.co": "Dental Implant Quote",
    "dentalimplantquote.com": "Dental Implant Quote (alias)",
    "getpulsari.com": "Pulsari",
    "ukheatpumpguide.com": "UK Heat Pump Guide",
    "getskinscore.com": "Skin Score",
    "nutridecrypte.com": "NutriDécrypte",
    "ratingcafe.com": "Rating Cafe",
    "lobservatoiredespros.com": "L'Observatoire des Pros",
}

# Brand names from sibling projects. Detecting them as plain strings in .astro /
# .ts / .js / .md / .json catches copy-paste contamination of legal pages, meta
# tags, OG images, CTAs, etc. "Zooplus" is flagged because it is the affiliate
# merchant wired to PetFoodRate ; BébéDécrypte uses Amazon + Greenweez only.
# Brand tokens , only include strings that are unambiguously a sibling
# project reference when they appear in runtime code. We deliberately avoid
# common French / English words that collide with the project names :
#   , "Adapte-toi" is a valid French imperative ("adapt yourself")
#   , "Econono" starts like "économique"
#   , "Mine de Teint" clashes with the "mine de rien" idiom
# For those ambiguous projects, the domain match + Supabase ref checks are
# enough to catch real contamination.
KNOWN_SIBLING_BRAND_TOKENS = {
    "BébéDécrypte": "BébéDécrypte",
    "BebeDecrypte": "BébéDécrypte",
    "bebedecrypte.com": "BébéDécrypte",
    "PetFoodRate": "PetFoodRate",
    "petfoodrate.com": "PetFoodRate",
    "DecrypteBot": "DecrypteBot",
    "Decryptebot": "DecrypteBot",
    "decryptebot.com": "DecrypteBot",
    "NutriDécrypte": "NutriDécrypte",
    "NutriDecrypte": "NutriDécrypte",
    "nutridecrypte.com": "NutriDécrypte",
    "Karmastro": "Karmastro",
    "karmastro.com": "Karmastro",
    "Score-Immo": "ScoreImmo",
    "ScoreImmo": "ScoreImmo",
    "score-immo.fr": "ScoreImmo",
    "Expert Menuiserie": "Expert Menuiserie",
    "expert-menuiserie.fr": "Expert Menuiserie",
    "Dental Implant Quote": "Dental Implant Quote",
    "dentalimplantquote.co": "Dental Implant Quote",
    "SkinScore": "GetSkinScore",
    "getskinscore.com": "GetSkinScore",
    "Pulsari": "Pulsari",
    "getpulsari.com": "Pulsari",
    "UK Heat Pump Guide": "UK Heat Pump Guide",
    "ukheatpumpguide.com": "UK Heat Pump Guide",
    "Rating Cafe": "Rating Cafe",
    "ratingcafe.com": "Rating Cafe",
    "L'Observatoire des Pros": "Observatoire des Pros",
    "lobservatoiredespros.com": "Observatoire des Pros",
}

# Only scan runtime source / content / public in this repo ; legal postmortems
# and audit notes stay allowed everywhere else.
RUNTIME_PATH_PREFIXES = (
    "site/src/", "site/public/", "site/functions/", "site/astro.config",
    "site/site.config", "src/", "public/", "functions/",
)

# Files and paths we never want to scan (binaries, generated assets, lockfiles,
# node_modules, this script itself).
IGNORE_DIRS = {
    ".git", "node_modules", "dist", ".astro", ".wrangler", ".next",
    "public/_astro", "coverage", ".cache",
    # Internal affiliate / merchant research notes that legitimately compare
    # shortlists across multiple STACK-2026 projects.
    "awin", "affiliate-research",
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    # The check script references sibling refs on purpose , skip.
    "check_cross_project_leaks.py",
    # Post-incident documentation may reference the offending project refs
    # by name (CLAUDE.md narrates the 2026-04-23 data leak).
    "CLAUDE.md",
    "README.md",
    "PIPELINE_MATRIX.md",
    "INCIDENT.md",
    "SESSION_AUDIT.md",
}
IGNORE_EXTS = {
    ".woff", ".woff2", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".webp",
    ".gif", ".ico", ".avif", ".mp4", ".webm", ".zip", ".tar", ".gz", ".pdf",
}

# Supabase ref = exactly 20 lowercase letters (current naming convention).
SUPABASE_REF_RE = re.compile(r"\b([a-z]{20})\.supabase\.co\b")
# Supabase JWT tokens carry the ref in their payload , decode-less detection
# via the `ref` claim regex.
JWT_REF_RE = re.compile(r'"ref":"([a-z]{20})"')


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.name in IGNORE_FILES:
            continue
        if p.suffix.lower() in IGNORE_EXTS:
            continue
        yield p


def scan(root: Path) -> list[dict]:
    violations: list[dict] = []
    self_ref = SELF_PROJECT["supabase_ref"]
    self_domain = SELF_PROJECT["domain"]
    allowed_refs = set(SELF_PROJECT.get("own_supabase_refs") or {self_ref})
    allowed_refs.add(self_ref)
    allowed_domains = set(SELF_PROJECT.get("own_domains") or {self_domain})
    allowed_domains.add(self_domain)
    own_tokens = set(SELF_PROJECT.get("own_tokens") or ())

    for f in iter_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Supabase ref inside a *.supabase.co URL
        for m in SUPABASE_REF_RE.finditer(text):
            ref = m.group(1)
            if ref in allowed_refs:
                continue
            sibling = KNOWN_SIBLING_SUPABASE_REFS.get(ref)
            violations.append(
                {
                    "file": str(f.relative_to(root)),
                    "line": text.count("\n", 0, m.start()) + 1,
                    "kind": "supabase-host",
                    "value": f"{ref}.supabase.co",
                    "owner": sibling or "unknown",
                }
            )

        # Supabase ref inside a JWT payload (anon / service keys)
        for m in JWT_REF_RE.finditer(text):
            ref = m.group(1)
            if ref in allowed_refs:
                continue
            sibling = KNOWN_SIBLING_SUPABASE_REFS.get(ref)
            violations.append(
                {
                    "file": str(f.relative_to(root)),
                    "line": text.count("\n", 0, m.start()) + 1,
                    "kind": "supabase-jwt-ref",
                    "value": ref,
                    "owner": sibling or "unknown",
                }
            )

        # Sibling domains mentioned in runtime code (HTML, TS, JS, Astro).
        # We only flag fully-qualified references inside src/public/functions.
        rel = str(f.relative_to(root))
        if rel.startswith(RUNTIME_PATH_PREFIXES):
            for domain, owner in KNOWN_SIBLING_DOMAINS.items():
                if domain in allowed_domains:
                    continue
                needle = f"//{domain}"
                idx = text.find(needle)
                if idx == -1:
                    continue
                violations.append(
                    {
                        "file": rel,
                        "line": text.count("\n", 0, idx) + 1,
                        "kind": "sibling-domain",
                        "value": domain,
                        "owner": owner,
                    }
                )

        # Known sibling raw Supabase refs outside URLs (sometimes written as
        # `const PROJECT_REF = "bhmmidfnovtkcxljjfpd"`).
        for ref, owner in KNOWN_SIBLING_SUPABASE_REFS.items():
            if len(ref) != 20:
                continue  # CF zone ID etc.
            idx = text.find(ref)
            if idx == -1:
                continue
            # Skip if the ref is part of the allow-list (main project + app split)
            if ref in allowed_refs:
                continue
            violations.append(
                {
                    "file": rel,
                    "line": text.count("\n", 0, idx) + 1,
                    "kind": "supabase-ref-literal",
                    "value": ref,
                    "owner": owner,
                }
            )

        # Sibling brand tokens in runtime source (catches "PetFoodRate" in
        # meta titles, legal copy, OG images, etc.). Skip tokens that
        # legitimately belong to the current project (SELF_PROJECT.own_tokens).
        if rel.startswith(RUNTIME_PATH_PREFIXES):
            for token, owner in KNOWN_SIBLING_BRAND_TOKENS.items():
                if token in own_tokens:
                    continue
                idx = text.find(token)
                if idx == -1:
                    continue
                violations.append(
                    {
                        "file": rel,
                        "line": text.count("\n", 0, idx) + 1,
                        "kind": "sibling-brand-token",
                        "value": token,
                        "owner": owner,
                    }
                )

    # Deduplicate identical tuples (file, line, value) to keep output readable.
    seen = set()
    deduped = []
    for v in violations:
        key = (v["file"], v["line"], v["value"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(v)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    violations = scan(root)

    if args.json:
        print(json.dumps({"project": SELF_PROJECT, "violations": violations}, indent=2))
    else:
        if not violations:
            print(f"OK : no cross-project leaks found (scanned {SELF_PROJECT['name']}).")
        else:
            print(
                f"FAIL : {len(violations)} cross-project reference(s) found in {SELF_PROJECT['name']}.\n"
                "This repo must ship with only its own project identity "
                f"({SELF_PROJECT['supabase_ref']} / {SELF_PROJECT['domain']}).\n"
            )
            for v in violations:
                print(f"  {v['file']}:{v['line']}  [{v['kind']}]  {v['value']}  , owner: {v['owner']}")
            print(
                "\nFix paths:\n"
                "  1. If the file is a copy-paste from another STACK-2026 repo, delete it or rewrite it.\n"
                "  2. For analytics, read PUBLIC_SUPABASE_URL / PUBLIC_SUPABASE_ANON_KEY from import.meta.env\n"
                "     and fail-closed if the URL does not match the pinned project ref.\n"
                "  3. If the sibling ref is legitimately needed (documentation, postmortem), move it to a\n"
                "     Markdown file listed in IGNORE_FILES at the top of this script.\n"
            )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
