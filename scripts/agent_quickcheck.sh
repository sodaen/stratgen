#!/usr/bin/env bash
set -Eeuo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"

echo "== Health =="; curl -fsS "$BASE/health" | jq .
echo "== OpenAPI =="; curl -fsS "$BASE/openapi.json" | jq -r '.info.title, ((.paths|keys|length|tostring) + " paths")'
echo "== Ollama tags =="; curl -fsS "$OLLAMA_HOST/api/tags" | jq -r '.models[].name' || true
echo "OK"
