#!/usr/bin/env bash
set -Eeuo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TOPIC_RAW="${1:-AI roadmap demo}"
K="${K:-5}"

echo "== RAG: add a fresh tiny doc =="
DERIVED="$HOME/stratgen/data/knowledge/derived"
mkdir -p "$DERIVED"
PHRASE="purple-elephant RAG smoketest $(date +%s)"
DOC="$DERIVED/agent_${RANDOM}.txt"
printf "Agent proof doc.\nKey: %s\n" "$PHRASE" > "$DOC"
curl -fsS -X POST "$BASE/knowledge/embed_local" >/dev/null && echo "embed_local OK"

echo "== Preview with sources =="
TOPIC_ENC=$(jq -rn --arg s "Short paragraph that mentions: $PHRASE" '$s|@uri')
PREV=$(curl -fsS "$BASE/content/preview_with_sources?topic=$TOPIC_ENC&k=$K")
echo "$PREV" | jq '{ok, snippet: ((.content // "")[:200] + "..."), top2: (.sources // [])[:2]}'

echo "== Draft (generate) =="
DRAFT=$(curl -fsS -X POST "$BASE/content/generate" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg p "One paragraph on: $TOPIC_RAW" '{prompt:$p, max_tokens:200}')")
echo "$DRAFT" | jq '{ok, has_text: ((.text // .content_map // "")|tostring|length>0)}'

echo "== Project + PPTX export =="
PID=$(curl -fsS -X POST "$BASE/projects/save" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg title "$TOPIC_RAW" '{title:$title, sections:["Intro","Plan","Next Steps"]}')" \
  | jq -r '.project.id')

R=$(curl -fsS -X POST "$BASE/pptx/render_from_project/$PID")
DL=$(jq -r '.url // ("/exports/download/" + (.path|split("/")|last))' <<<"$R")
OUT="/tmp/$PID.pptx"
curl -fSLo "$OUT" "$BASE$DL"
file "$OUT" | grep -qi 'PowerPoint' && echo "OK: $OUT" || { echo "Export failed"; exit 1; }
