#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

say() { printf '\n— %s —\n' "$*"; }

say "health"
curl -sS "$API/health" "${HDR[@]}" | jq -r .status

say "exports/list"
curl -sS "$API/exports/list" "${HDR[@]}" | jq '.count'

say "compose"
REQ=$(jq -n --arg c "Acme GmbH" --arg t "Go-to-Market 2026 (RAG)" --arg q "ISO27001 SOC2 ROI 90 Tage" \
  '{customer_name:$c, topic:$t, query:$q}')
CMP=$(curl -sS -X POST "$API/content/compose" "${HDR[@]}" -H 'Content-Type: application/json' -d "$REQ")
TITLE=$(printf '%s' "$CMP" | jq -r '.title // "Deck"')
TITLE=$(python3 - "$TITLE" <<'PY'
import re,sys; t=sys.argv[1]; print(re.sub(r'( \(RAG\))(?:\s*\(RAG\))+', r'\1', t))
PY
)
say "render"
curl -sS -X POST -H "Content-Type: application/json" --data "{}" "$API/pptx/render" "${HDR[@]}" -H 'Content-Type: application/json' \
  -d "$(printf '%s' "$CMP" | jq --arg T "$TITLE" '{title:$T, plan:.plan}')"

say "latest + head/get"
BN=$(curl -sS "$API/exports/latest" "${HDR[@]}" | jq -r '.latest.name')
echo "latest: $BN"
curl -sI --get --data-urlencode "name=$BN" "${HDR[@]}" "$API/exports/download" | sed -n '1,8p'
curl -s  --get --data-urlencode "name=$BN" "${HDR[@]}" -o "/tmp/$BN" "$API/exports/download"
ls -lh "/tmp/$BN" | sed -n '1p'
