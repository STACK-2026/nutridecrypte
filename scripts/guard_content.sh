#!/usr/bin/env bash
# Local blocking content gate for the build (STACK-2026 content_guard.py).
# - Checks the .md/.mdx changed in the last commit (git diff HEAD~1 HEAD).
# - Falls back to a full scan of the blog collection when no diff is available
#   (shallow clone / first commit / not a git checkout).
# - Skips cleanly (exit 0) when python3 is unavailable so the build never
#   breaks on environments without Python.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GUARD="$SCRIPT_DIR/content_guard.py"
# Blog collection only: BlogLayout emits the title as the page H1, so a body
# "# " heading is a true double-H1.
CONTENT_DIR="$REPO_ROOT/site/src/content/blog"

if ! command -v python3 >/dev/null 2>&1; then
  echo "content guard: python3 not found — skipped."
  exit 0
fi
if [ ! -f "$GUARD" ]; then
  echo "content guard: $GUARD missing — skipped."
  exit 0
fi

cd "$REPO_ROOT"
changed=""
if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
  changed="$(git diff --name-only --diff-filter=ACMR HEAD~1 HEAD -- 'site/src/content/blog/**/*.md' 'site/src/content/blog/**/*.mdx' 'site/src/content/blog/*.md' 2>/dev/null || true)"
fi

targets=()
if [ -n "$changed" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] && [ -f "$REPO_ROOT/$f" ] && targets+=("$REPO_ROOT/$f")
  done <<< "$changed"
fi

if [ "${#targets[@]}" -eq 0 ]; then
  echo "content guard: no changed blog .md/.mdx — full scan of $CONTENT_DIR"
  exec python3 "$GUARD" --check "$CONTENT_DIR"
fi

echo "content guard: checking ${#targets[@]} changed file(s)"
exec python3 "$GUARD" --check "${targets[@]}"
