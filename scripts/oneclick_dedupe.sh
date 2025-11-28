#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

CUSTOMER="${CUSTOMER:-Acme GmbH}"
TOPIC="${TOPIC:-Go-to-Market 2026 (RAG)}"
QUERY="${QUERY:-ISO27001 SOC2 ROI 90 Tage}"

# Compose-Body via jq bauen (sauberes JSON, kein Heredoc)
REQ=$(jq -n --arg c "$CUSTOMER" --arg t "$TOPIC" --arg q "$QUERY" \
  '{customer_name:$c, topic:$t, query:$q}')

RESP=$(curl -sS -X POST "$API/content/compose" "${HDR[@]}" \
  -H 'Content-Type: application/json' -d "$REQ")

# Titel extrahieren + "(RAG)"-Dedupe
TITLE_ORIG=$(printf '%s' "$RESP" | jq -r '.title // "Deck"')
TITLE=$(python3 - "$TITLE_ORIG" <<'PY'
import re,sys
t=sys.argv[1]
# "(RAG) (RAG)" → "(RAG)"; auch dreifach etc.
print(re.sub(r'( \(RAG\))(?:\s*\(RAG\))+', r'\1', t))
PY
)

# Render-Request: übernehme den Plan aus Compose, Title ersetzen
RENDER_REQ=$(printf '%s' "$RESP" | jq --arg T "$TITLE" '{title:$T, plan:.plan}')

RENDER=$(curl -sS -X POST -H "Content-Type: application/json" --data "{}" "$API/pptx/render" "${HDR[@]}" \
  -H 'Content-Type: application/json' -d "$RENDER_REQ")

echo "$RENDER" | jq .

# Latest holen (basename) und HEAD/GET testen
BN=$(curl -sS "$API/exports/latest" "${HDR[@]}" | jq -r '.latest.name')
echo "Latest: $BN"

echo "-- HEAD --"
curl -sI --get --data-urlencode "name=$BN" "${HDR[@]}" "$API/exports/download" | sed -n '1,8p'

OUT="/tmp/$BN"
echo "-- GET  -- (-> $OUT)"
curl -s --get --data-urlencode "name=$BN" "${HDR[@]}" -o "$OUT" "$API/exports/download"
ls -lh "$OUT"
