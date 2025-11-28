#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
DERIVED="${DERIVED:-$HOME/stratgen/data/knowledge/derived}"
PHRASE="${1:-purple-elephant RAG smoketest $(date +%s)}"
DOC="$DERIVED/rag_smoke_${RANDOM}.txt"

mkdir -p "$DERIVED"
printf "This doc proves the pipeline.\nKey: %s\n" "$PHRASE" > "$DOC"
echo "📄 $DOC"

curl -fsS -X POST "$BASE/knowledge/embed_local" >/dev/null && echo "embed_local OK"
Q=$(jq -rn --arg s "$PHRASE" '$s|@uri')
curl -fsS "$BASE/knowledge/search_semantic?q=$Q&k=5" \
 | jq '{top3: ((._hits // .hits // .results // .items // .sources // [])[:3])}'
