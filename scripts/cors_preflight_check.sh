#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
ORIGINS=(
  "http://localhost:5173"
  "http://127.0.0.1:5173"
  "http://localhost:4173"
  "http://127.0.0.1:4173"
)
for o in "${ORIGINS[@]}"; do
  echo "== Preflight from $o"
  curl -s -o >(grep -i '^Access-Control-' || true) -D - -X OPTIONS "$BASE/projects" \
    -H "Origin: $o" -H 'Access-Control-Request-Method: GET' >/dev/null
done
