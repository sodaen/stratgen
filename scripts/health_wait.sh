#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
for i in {1..60}; do
  if curl -fsS "$BASE/health" >/dev/null; then
    echo "health OK ($BASE)"; exit 0
  fi
  sleep 1
done
echo "health TIMEOUT ($BASE)" >&2
exit 1
