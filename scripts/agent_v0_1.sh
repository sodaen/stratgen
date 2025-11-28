#!/usr/bin/env bash
set -Eeuo pipefail
trap 'stty sane || true' EXIT ERR

BASE="${BASE:-http://127.0.0.1:8011}"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
MODEL="${LLM_MODEL:-mistral}"
TOPIC_RAW="${1:-AI roadmap demo}"
K="${K:-5}"

echo "== RAG: seed tiny evidence =="
DERIVED="$HOME/stratgen/data/knowledge/derived"; mkdir -p "$DERIVED"
PHRASE="purple-elephant RAG smoketest $(date +%s)"
printf "Agent proof doc.\nKey: %s\n" "$PHRASE" > "$DERIVED/agent_${RANDOM}.txt"
curl -fsS -X POST "$BASE/knowledge/embed_local" >/dev/null || true

echo "== Preview with sources =="
TOPIC=$(jq -rn --arg s "Short paragraph that mentions: $PHRASE" '$s|@uri')
PREV=$(curl -fsS "$BASE/content/preview_with_sources?topic=$TOPIC&k=$K")
echo "$PREV" | jq '{ok, snippet:(.content[0:180]+"…"), top2:(.sources[:2])}'
CTX=$(jq -r '.content // ""' <<<"$PREV")

echo "== Draft (content/generate) =="
PROMPT=$'Write one crisp paragraph on: '"$TOPIC_RAW"$'\n\nIncorporate this context where useful:\n'"$CTX"
DRAFT=$(curl -fsS -X POST "$BASE/content/generate" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg p "$PROMPT" '{prompt:$p, max_tokens:220}')")
TEXT=$(jq -r '.text // .content_map.intro // ""' <<<"$DRAFT")

echo "== Revise (Ollama) =="
REV_PROMPT=$'Revise the following paragraph: make it clearer, more actionable, and keep factual claims cautious.\n\n---\n'"$TEXT"
REVISED=$(curl -fsS "$OLLAMA_HOST/api/generate" \
  -d "$(jq -n --arg m "$MODEL" --arg p "$REV_PROMPT" '{model:$m,prompt:$p,stream:false}')" \
  | jq -r '.response')

printf "\n== Draft ==\n%s\n" "$TEXT"
printf "\n== Revised ==\n%s\n" "$REVISED"

echo "== Project + PPTX =="
PID=$(curl -fsS -X POST "$BASE/projects/save" -H 'Content-Type: application/json' \
  -d "$(jq -n --arg title "$TOPIC_RAW" '{title:$title, sections:["Intro","Plan","Next Steps"]}')" \
  | jq -r '.project.id')

R=$(curl -fsS -X POST "$BASE/pptx/render_from_project/$PID")
DL=$(jq -r '.url // ("/exports/download/" + (.path|split("/")|last))' <<<"$R")
OUT="/tmp/$PID.pptx"
curl -fSLo "$OUT" "$BASE$DL"
if file "$OUT" | grep -q 'PowerPoint'; then
  echo "✅ PPTX: $OUT"
else
  echo "⚠️ PPTX check failed"; file "$OUT"
fi
