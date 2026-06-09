# Content guard — nutridecrypte

## Role

`scripts/content_guard.py` is the STACK-2026 fleet-wide content gate. It catches the
recurring blog-auto defects **before** they reach production:

1. tool-call / generation artifacts leaked into content (`</content>`, `</invoke>`,
   `<function_calls>`, `<|...|>`, …) — these have broken whole builds across the parc.
2. duplicated frontmatter echoed into the body.
3. meta length: `title > 65` (flag-only), `description > 180` (clamped in `--fix`).
4. a top-level `# ` H1 inside the body => double H1 (the blog layout already emits the
   title as the page H1).
5. mojibake (`Ã©`, `â€™`, `Â`, `ðŸ…`).
6. em-dash / en-dash in body (parc YMYL rule — already a content rule here: no `—`/`–`).

## Why

Articles are generated via Gemini 2.5 Pro and occasionally leak generation artifacts,
echo frontmatter, ship over-long meta, or emit a second `#` H1. Any of these can degrade
SEO or break the Astro build. This guard is the deterministic backstop.

## Scope: blog only

The guard is scoped to `site/src/content/blog`. `BlogLayout` emits the article title as
the page `<h1>`, so a body `# ` is a genuine double-H1. (nutridecrypte's product/`/vs/`
pages are generated from the VPS Postgres DB, not from `src/content`.)

## FAQ

FAQPage JSON-LD is already emitted by `BlogLayout` when the frontmatter carries a `faq`
array (`{q,a}`), which also renders the visible accordion. No FAQ change was needed; the
guard does not touch FAQ wiring.

## Prebuild (local blocking gate)

`site/package.json` wires:

- `guard:content` → `bash ../scripts/guard_content.sh`
- `prebuild` → `npm run guard:content` (npm runs it automatically before `build`)

`scripts/guard_content.sh`:

- checks the `.md`/`.mdx` changed in the **last commit** (`git diff HEAD~1 HEAD`),
  restricted to `site/src/content/blog`;
- falls back to a **full scan** of `site/src/content/blog` when there is no diff;
- **skips cleanly** (exit 0) when `python3` is unavailable so the build never breaks.

A blocking defect makes `prebuild` exit non-zero, which aborts `npm run build`.

## Build & deploy note (Tier-2 site)

This is a T2 site: the build reads the VPS Postgres `db_nutridecrypte` over the CF
tunnel, `deploy-site.yml` is `disabled_manually`, and deploy is a manual local
`wrangler pages deploy`. The content guard runs as the `prebuild` step regardless of the
DB; only the Astro build itself needs `DATABASE_URL`.

## Re-verify

```bash
# content gate only (no DB needed)
python3 scripts/content_guard.py --check site/src/content/blog
python3 scripts/content_guard.py --fix  site/src/content/blog   # non-destructive backfill

# full build (needs the VPS tunnel + DATABASE_URL, see CLAUDE.md)
cd site && DATABASE_URL=$VPS_PG_NUTRIDECRYPTE_URL npm run build  # prebuild gate then build
```
