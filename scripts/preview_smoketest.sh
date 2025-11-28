#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TOPIC_RAW="${1:-Short paragraph that mentions: purple-elephant RAG smoketest $(date +%s)}"
TOPIC=$(jq -rn --arg s "$TOPIC_RAW" '$s|@uri')

echo "== preview"
curl -fsS "$BASE/content/preview?topic=$TOPIC&k=3" \
 | jq '{ok, content_snippet: ((.content // .text // "")[0:160] + "...")}'

echo "== preview_with_sources"
curl -fsS "$BASE/content/preview_with_sources?topic=$TOPIC&k=3" \
 | jq '{ok, content_snippet: ((.content // .text // "")[0:160] + "..."), top3: (.sources[:3])}'
