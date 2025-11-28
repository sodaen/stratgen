#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
PROMPT="${1:-Write one sentence that includes: purple-elephant RAG smoketest $(date +%s)}"
PAYLOAD=$(jq -n --arg p "$PROMPT" '{prompt:$p, max_tokens: 220}')
curl -fsS -X POST "$BASE/content/generate" -H 'Content-Type: application/json' -d "$PAYLOAD" \
| jq '{ok, text: (.text // .content // .content_map // .response // .)}'
