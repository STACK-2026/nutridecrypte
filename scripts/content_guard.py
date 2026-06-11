#!/usr/bin/env python3
"""
content_guard.py — STACK-2026 fleet-wide content gate (root fix, 2026-06-09).

ONE guard, replicated across the parc, that catches the recurring blog-auto
defects BEFORE they go live (the ones that slipped past seo-guardrails.yml +
publish.py for months):

  1. tool-call / generation artifacts leaked into content
     (</content>, </invoke>, <function_calls>, <*>, stray code fences)
     -> these have broken whole builds (foyer 09/06).
  2. duplicated frontmatter echoed into the body (commandeici 09/06).
  3. meta length: title > 65, meta description > 180 (SERP truncation).
  4. a top-level `# ` H1 inside the body => double H1 (template already emits
     the title as H1) (decryptebot 09/06).
  5. mojibake (Ã©, â€™, Â, ðŸ...).
  6. em-dash / en-dash in body (parc YMYL rule) — backstop.
  7. ACCENT_LOW: a French body shipped with near-zero diacritics (ASCII-folded).
     Always-on, language-aware (never fires on EN/ES/PT). Root leak on 11/06
     (adapte-toi/Stanford at density 0.0). Blocking; re-accent with
     reaccent_gemini.py (not auto-fixable here).
  8. (optional, --check-links) dead internal/external links.

ACCENT_LOW is now a native, always-on check. --with-accents ADDITIONALLY shells
out to scripts/check_accents.py (its high-frequency folded-word signal) for the
whole --site dir; keep it for belt-and-suspenders in CI.

Modes:
  --check   exit 1 if any blocking defect is found (use in CI / seo-guardrails).
  --fix     auto-fix the deterministic defects in place (idempotent), report the
            rest. Safe to run every build and as a one-shot backfill.

Usage:
  python3 content_guard.py --check  src/content            # CI gate
  python3 content_guard.py --fix    src/content/blog/x.md  # fix one/many
  python3 content_guard.py --check --with-accents --site guidebanque src/content
  python3 content_guard.py --fix --check-links src/content/.../today.md

Standalone: stdlib only. Title length is FLAG-only by default (auto-shortening a
title is destructive); description IS clamped at a word boundary in --fix.
"""
from __future__ import annotations
import argparse, os, re, sys, subprocess
from pathlib import Path

TITLE_MAX = 65
DESC_MAX = 180

# 1. tool-call / generation artifacts. These must NEVER appear in content.
ARTIFACT_PATTERNS = [
    r"</?content>",
    r"</?invoke\b[^>]*>",
    r"</?function_calls>",
    r"</?function_results>",
    r"</?parameter\b[^>]*>",
    r"</?antml:[^>]*>",
    r"<\|[^>]*\|>",                     # <|im_start|> style
]
ARTIFACT_RE = re.compile("|".join(ARTIFACT_PATTERNS), re.IGNORECASE)

MOJIBAKE_RE = re.compile(r"Ã[©¨ª«¢ ]|â€™|â€|â€|â€“|â€”|Â[  ]|Ã©|ðŸ|Ã¯Â¿Â½")
EM_EN_RE = re.compile(r"[–—]")

# ---- accent guard: deaccented (ASCII-folded) French detector, always-on ----
# Native, language-aware version of check_accents.py's density signal. A FAIL on
# its own (no MIN_HITS wordlist needed): a French body with near-zero diacritics
# is the recurring leak (adapte-toi/Stanford 11/06 shipped at density 0.0). Made
# language-aware so it NEVER fires on the parc's English/Spanish/Portuguese
# articles (their FR accent density is legitimately ~0).
ACCENTS = set("éèàêôîûçùâëïüœæÉÈÀÊÔÎÛÇÙÂËÏÜ")
MIN_ACCENT_DENSITY = 8       # accented chars / 1000 prose chars; healthy FR = 25-45
MIN_FOLDED_HITS = 4          # folded-FR words to confirm the body is French
MIN_PROSE_LEN = 500          # below this the body is too short to judge
# French words that are almost ALWAYS accented; their appearance in ASCII-folded
# form (with the accented form ABSENT) is the language-safe signal for "this is
# deaccented French". Chosen to NOT collide with English/Spanish/Italian/Portuguese
# (no Latin homographs like "experience"/"education"/"difference"). A folded body
# in another language scores ~0 here, so the gate never misfires on EN/ES/IT/PT.
FOLDED_FR = [
    ("securite", "sécurité"), ("methode", "méthode"), ("donnees", "données"),
    ("fiscalite", "fiscalité"), ("autorite", "autorité"), ("qualite", "qualité"),
    ("propriete", "propriété"), ("societe", "société"), ("epargne", "épargne"),
    ("prelevement", "prélèvement"), ("interet", "intérêt"), ("considere", "considéré"),
    ("integre", "intégré"), ("realise", "réalisé"), ("verifie", "vérifié"),
    ("decede", "décédé"), ("deces", "décès"), ("heritier", "héritier"),
    ("procedure", "procédure"), ("remunere", "rémunéré"), ("numerique", "numérique"),
    ("strategie", "stratégie"), ("eligibilite", "éligibilité"),
    ("responsabilite", "responsabilité"), ("necessite", "nécessité"),
    ("possibilite", "possibilité"), ("activite", "activité"), ("etude", "étude"),
    ("etape", "étape"), ("evenement", "événement"), ("etranger", "étranger"),
    ("egalement", "également"), ("deja", "déjà"), ("tres", "très"),
    ("apres", "après"), ("etablissement", "établissement"), ("controle", "contrôle"),
    ("numero", "numéro"), ("reel", "réel"), ("reseau", "réseau"),
    ("requete", "requête"), ("francais", "français"), ("generale", "générale"),
    ("reference", "référence"), ("frequence", "fréquence"), ("specificite", "spécificité"),
    ("anneee", "année"), ("annee", "année"), ("regulier", "régulier"),
    ("complementaire", "complémentaire"), ("preference", "préférence"),
]


def prose_only(body: str) -> str:
    """Body stripped of fenced/inline code, URLs and markdown link targets
    (these are never accented and would dilute the density signal)."""
    t = re.sub(r"```.*?```", " ", body, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\]\([^)]*\)", " ", t)
    return t


FM_RE = re.compile(r"^(---\s*\n)(.*?)(\n---\s*\n)", re.S)


def split_fm(text: str):
    """Return (head, fm_inner, fence, body) or (None, None, None, text)."""
    m = FM_RE.match(text)
    if not m:
        return None, None, None, text
    return m.group(1), m.group(2), m.group(3), text[m.end():]


def _looks_like_frontmatter(inner: str) -> bool:
    """True only if `inner` is a real YAML frontmatter block (majority of
    non-blank lines are `key: value`), NOT a prose section that merely happens
    to sit between two `---` markdown horizontal rules (e.g. a TL;DR or a
    Sommaire opening with `---`). Without this guard the greedy `---...---`
    match eats the whole article body (karmastro regression, 09/06)."""
    lines = [ln for ln in inner.splitlines() if ln.strip()]
    if not lines:
        return False
    kv = sum(1 for ln in lines if re.match(r"^\s*[A-Za-z_][\w-]*:\s", ln))
    # require at least 2 key: lines AND that they dominate the block; a single
    # stray `Mot : valeur` inside prose must never qualify.
    return kv >= 2 and kv >= len(lines) * 0.8


def strip_echoed_frontmatter(body: str) -> str:
    """Drop a frontmatter block echoed into the body (fenced or bare key: run).

    Only strips a leading `---...---` block when its inner content actually
    looks like frontmatter; a body that opens with a markdown `<hr>` followed
    by prose is left untouched."""
    b = body.lstrip("\n")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", b, re.S)
    if m and _looks_like_frontmatter(m.group(1)):
        return b[m.end():].lstrip("\n")
    m = re.match(r"^(?:[A-Za-z_][\w-]*:.*\n)+---\s*\n", b)
    if m:
        return b[m.end():].lstrip("\n")
    return body


def clamp_value(val: str, limit: int) -> str:
    if len(val) <= limit:
        return val
    cut = val[:limit]
    sp = cut.rfind(" ")
    if sp > limit * 0.6:
        cut = cut[:sp]
    return cut.rstrip(" ,;:.-–—")


def fm_field(fm_inner: str, key: str):
    # Returns (match, DECODED logical value, source_quote). The value is decoded
    # to its logical content (YAML un-escaped) so the caller can re-encode it
    # safely regardless of the original quoting style.
    m = re.search(rf'(?m)^(\s*{re.escape(key)}:\s*)"((?:[^"\\]|\\.)*)"\s*$', fm_inner)
    if m:
        return m, m.group(2).replace('\\"', '"').replace("\\\\", "\\"), '"'
    m = re.search(rf"(?m)^(\s*{re.escape(key)}:\s*)'((?:[^']|'')*)'\s*$", fm_inner)
    if m:
        return m, m.group(2).replace("''", "'"), "'"
    m = re.search(rf"(?m)^(\s*{re.escape(key)}:\s*)(?![\"'\[{{])(.+?)\s*$", fm_inner)
    if m:
        return m, m.group(2), ""
    return None, None, None


def analyze(path: Path, fix: bool, check_links: bool):
    """Return (issues, fixed_count, new_text_or_None)."""
    raw = path.read_text(encoding="utf-8")
    text = raw
    issues = []
    fixes = []

    # ---- 1. tool-call / generation artifacts (anywhere) ----
    arts = ARTIFACT_RE.findall(text)
    if arts:
        issues.append(("ARTIFACT", f"{len(arts)} tool-call/generation tag(s) leaked, e.g. {arts[:3]}"))
        if fix:
            text = ARTIFACT_RE.sub("", text)
            # collapse the blank lines they leave behind at EOF
            text = re.sub(r"\n{3,}", "\n\n", text).rstrip("\n") + "\n"
            fixes.append("stripped tool-call artifacts")

    head, fm_inner, fence, body = split_fm(text)

    # ---- 2. duplicated frontmatter echoed into body ----
    if head is not None:
        new_body = strip_echoed_frontmatter(body)
        if new_body != body:
            issues.append(("FRONTMATTER_DUP", "frontmatter echoed into body"))
            if fix:
                body = new_body
                fixes.append("removed duplicated frontmatter from body")

    # ---- 3. meta length (title flag-only, description clamped) ----
    if fm_inner is not None:
        tm, tval, tq = fm_field(fm_inner, "title")
        if tval is not None and len(tval) > TITLE_MAX:
            issues.append(("TITLE_LONG", f"title {len(tval)}c > {TITLE_MAX} (flag-only)"))
        dm, dval, dq = fm_field(fm_inner, "description")
        if dval is not None:
            new_val = dval
            # bug-#3 residue: `''` inside a DOUBLE-quoted description is a literal
            # double apostrophe (renders "d''un") — never intentional in double
            # quotes; it comes from a clamp that re-emitted single-quote source
            # without decoding. Collapse it. (In single-quote source fm_field has
            # already decoded '' -> ', so this only catches the artifact.)
            if dq == '"' and "''" in new_val:
                new_val = new_val.replace("''", "'")
                issues.append(("DESC_QUOTE_ARTIFACT", "double-quoted description contains '' (renders d''un)"))
            if len(new_val) > DESC_MAX:
                issues.append(("DESC_LONG", f"description {len(new_val)}c > {DESC_MAX}"))
                new_val = clamp_value(new_val, DESC_MAX)
            if fix and new_val != dval:
                # re-emit as a double-quoted YAML scalar (valid for any source
                # quote style) so apostrophes, colons and question marks survive.
                esc = new_val.replace("\\", "\\\\").replace('"', '\\"')
                fm_inner = fm_inner[:dm.start()] + f'{dm.group(1)}"{esc}"' + fm_inner[dm.end():]
                fixes.append(f"normalized description -> {len(new_val)}c")

    # ---- 4. body-level H1 (=> double H1 with template title) ----
    h1s = re.findall(r"(?m)^#[ \t]+\S", body)
    if h1s:
        issues.append(("BODY_H1", f"{len(h1s)} top-level '# ' heading(s) in body (double H1)"))
        if fix:
            body = re.sub(r"(?m)^#([ \t]+\S)", r"##\1", body)  # demote # -> ##
            fixes.append(f"demoted {len(h1s)} body H1 to H2")

    # ---- 5. mojibake ----
    if MOJIBAKE_RE.search(body) or (fm_inner and MOJIBAKE_RE.search(fm_inner)):
        issues.append(("MOJIBAKE", "mojibake sequences present (manual fix)"))

    # ---- 6. em/en-dash in body (backstop) ----
    if EM_EN_RE.search(body):
        n = len(EM_EN_RE.findall(body))
        issues.append(("EM_DASH", f"{n} em/en-dash in body"))
        if fix:
            body = body.replace(" — ", ", ").replace("—", ", ")
            body = body.replace(" – ", "-").replace("–", "-")
            fixes.append("normalized em/en-dashes")

    # ---- 7. deaccented French body (language-safe accent density gate) ----
    # Two signals, both required: (a) accent density below floor, AND (b) several
    # normally-accented French words present in folded form (their accented form
    # absent). (b) makes it French-specific so EN/ES/IT/PT never trip the gate.
    # Not auto-fixable (re-accent needs reaccent_gemini.py) -> blocking FAIL.
    prose = prose_only(body)
    if len(prose) >= MIN_PROSE_LEN:
        acc = sum(1 for c in prose if c in ACCENTS)
        density = acc * 1000 / len(prose)
        if density < MIN_ACCENT_DENSITY:
            low = prose.lower()
            folded = sum(1 for ascii_f, acc_f in FOLDED_FR
                         if re.search(rf"\b{ascii_f}\b", low) and acc_f not in low)
            if folded >= MIN_FOLDED_HITS:
                issues.append(("ACCENT_LOW",
                    f"French body, accent density {density:.1f}/1000 < {MIN_ACCENT_DENSITY} "
                    f"({folded} folded-FR words) — ASCII-folded, run reaccent_gemini.py"))

    # reassemble
    if head is not None:
        new_text = f"{head}{fm_inner}{fence}{body}"
    else:
        new_text = body
    changed = fix and new_text != raw

    # ---- 7. optional link check (network) ----
    if check_links:
        issues.extend(_check_links(new_text if fix else raw, path))

    return issues, fixes, (new_text if changed else None)


def _check_links(text: str, path: Path):
    import urllib.request, urllib.error
    out = []
    hrefs = set(re.findall(r"\]\((https?://[^)\s]+)\)", text))
    hrefs |= set(re.findall(r'href=["\'](https?://[^"\']+)["\']', text))
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    for url in sorted(hrefs):
        try:
            req = urllib.request.Request(url, headers=UA, method="HEAD")
            code = urllib.request.urlopen(req, timeout=12).status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        if code in (404, 410) or code == 0:
            out.append(("DEAD_LINK", f"{code} {url}"))
    return out


def main():
    ap = argparse.ArgumentParser(description="STACK-2026 content guard")
    ap.add_argument("paths", nargs="+", help="files or dirs (scans *.md/*.mdx)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="exit 1 on blocking defects")
    g.add_argument("--fix", action="store_true", help="auto-fix in place")
    ap.add_argument("--with-accents", action="store_true", help="also run check_accents.py")
    ap.add_argument("--site", default=None, help="site slug (for --with-accents)")
    ap.add_argument("--check-links", action="store_true", help="HEAD-check external links (slow)")
    args = ap.parse_args()

    files = []
    for p in args.paths:
        pp = Path(p)
        if pp.is_dir():
            files += sorted(pp.rglob("*.md")) + sorted(pp.rglob("*.mdx"))
        elif pp.exists():
            files.append(pp)
    # blocking = anything except the flag-only TITLE_LONG / TITLE_TRUNCATED?
    NON_BLOCKING = {"TITLE_LONG", "DESC_QUOTE_ARTIFACT"}

    total_block = 0
    total_fixed = 0
    for f in files:
        issues, fixes, new_text = analyze(f, args.fix, args.check_links)
        if args.fix and new_text is not None:
            f.write_text(new_text, encoding="utf-8")
            total_fixed += 1
        if issues:
            blocking = [i for i in issues if i[0] not in NON_BLOCKING]
            total_block += len(blocking)
            tag = "FIXED" if (args.fix and fixes) else ("FAIL" if blocking else "warn")
            print(f"[{tag}] {f}")
            for code, msg in issues:
                print(f"    - {code}: {msg}")
            if args.fix and fixes:
                for fx in fixes:
                    print(f"    -> {fx}")

    # accents delegated to the existing parc script
    if args.with_accents and args.site:
        acc = Path(__file__).with_name("check_accents.py")
        if acc.exists():
            r = subprocess.run([sys.executable, str(acc), "--site", args.site])
            if r.returncode != 0 and args.check:
                total_block += 1

    if args.check and total_block:
        print(f"\nCONTENT GUARD: {total_block} blocking defect(s).", file=sys.stderr)
        sys.exit(1)
    print(f"\nCONTENT GUARD OK ({len(files)} file(s)" +
          (f", {total_fixed} fixed" if args.fix else "") + ").")


if __name__ == "__main__":
    main()
