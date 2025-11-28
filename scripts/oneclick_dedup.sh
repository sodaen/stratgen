#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

CUSTOMER="${1:-Acme GmbH}"
TOPIC="${2:-Go-to-Market 2026 (RAG)}"
QUERY="${3:-probe}"

# Compose
REQ=$(jq -n --arg c "$CUSTOMER" --arg t "$TOPIC" --arg q "$QUERY" \
       '{customer_name:$c, topic:$t, query:$q}')
RESP=$(curl -sS "${HDR[@]}" -H "Content-Type: application/json" \
       -d "$REQ" "$API/content/compose")

# (RAG)-Dedupe (belässt exakt 1x "(RAG)")
RESP2=$(jq '
  .title as $orig
  | ($orig // "") as $t
  | ($t | gsub("\\(RAG\\)([[:space:]]*\\(RAG\\))+";"(RAG)")) as $dedup
  | .title = $dedup
  | (if (.plan|length>0) and (.plan[0].kind=="title") then
       .plan[0].title = $dedup
     else . end)
' <<<"$RESP")

TITLE=$(jq -r '.title' <<<"$RESP2")
[ "$TITLE" = "null" ] && TITLE="Deck"
OUT_BN="deck-$(date +%Y%m%d-%H%M%S).pptx"
OUT_PATH="data/exports/$OUT_BN"

RENDER=$(jq --arg out "$OUT_PATH" \
  '{title:.title, plan:.plan, out_path:$out}' <<<"$RESP2")

# Render
RRESP=$(curl -sS "${HDR[@]}" -H "Content-Type: application/json" \
        -d "$RENDER" "$API/pptx/render")
echo "$RRESP" | jq .

# HEAD + GET Download (Basename; Server encodet korrekt)
BN="$OUT_BN"
echo "HEAD:"
curl -sI --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p'
echo "GET -> /tmp/$BN"
curl -s --get --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download"
ls -lh "/tmp/$BN"
