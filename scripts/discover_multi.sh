#!/usr/bin/env bash
# Sequential discovery across priority French supermarket categories.
# Polite 3s delay between pages, 10s delay between categories.

set -u
cd "$(dirname "$0")/.."

CATEGORIES=(
  "breakfast-cereals:700"
  "biscuits:800"
  "sodas:600"
  "chocolates:600"
  "crisps:400"
  "cheeses:500"
  "breads:500"
  "charcuteries:400"
  "breakfast-beverages:300"
  "dairy-desserts:300"
)

for entry in "${CATEGORIES[@]}"; do
  CAT="${entry%%:*}"
  LIMIT="${entry##*:}"
  OUT="pending/off_${CAT}_france.jsonl"
  # Skip if already have a non-empty file
  if [ -s "$OUT" ]; then
    echo "[skip] $CAT already has $(wc -l < "$OUT") products in $OUT"
    continue
  fi
  echo "[run] $CAT (limit $LIMIT)"
  python3 scripts/discover_off.py --category "$CAT" --country france --limit "$LIMIT" --page-size 50 || true
  echo "[sleep 10s between categories]"
  sleep 10
done

echo "DONE all categories."
ls -la pending/
