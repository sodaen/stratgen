#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"

echo "== title & count"
curl -fsS "$BASE/openapi.json" | jq -r '.info.title + " – " + ((.paths|length)|tostring) + " paths"'

echo "== DUP operationIds?"
DUPS=$(curl -fsS "$BASE/openapi.json" | jq -r '
  .paths | to_entries[]
  | .value | to_entries[]
  | .value.operationId // empty' | sort | uniq -c | awk '$1>1{print}')
if [ -n "$DUPS" ]; then
  echo "❌ duplicates:"; echo "$DUPS"
else
  echo "✅ none"
fi
