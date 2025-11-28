#!/usr/bin/env bash
set -u
set -o pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

echo "— health —"
curl -sS "${HDR[@]}" "$API/health" | jq -r .status || echo "[warn] health fehlgeschlagen"

echo "— upload demo bundle —"
scripts/upload_with_manifest.sh samples/wave1_upload_demo assets_tmp/wave1_bundle.zip

echo "— compose —"
CRES="$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
  -d '{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"ISO27001 SOC2 ROI <90T; benutze hochgeladene Assets wenn möglich"}' \
  "$API/content/compose" || true)"
echo "$CRES" | jq '.title, (.plan|length)' 2>/dev/null || true

TITLE="$(printf '%s' "$CRES" | jq -r '.title // empty' 2>/dev/null || true)"
PLAN_JSON="$(printf '%s' "$CRES" | jq -c '.plan // []' 2>/dev/null || echo '[]')"

# Fallback-Plan, falls Compose nichts Sinnvolles liefert
if [ -z "${TITLE:-}" ] || [ "$PLAN_JSON" = "null" ] || [ -z "${PLAN_JSON:-}" ]; then
  TITLE="${TITLE:-Go-to-Market 2026 (RAG) – Acme GmbH}"
  PLAN_JSON='[
    {"kind":"title","layout_hint":"Title Slide","title": "'"$TITLE"'"},
    {"kind":"agenda","layout_hint":"Title and Content","title":"Agenda","bullets":["Kontext & Ziele","Insights","Strategie","KPIs","Roadmap"]}
  ]'
fi

OUT="data/exports/deck-$(date +%Y%m%d-%H%M%S).pptx"
RBODY="$(jq -c -n --arg title "$TITLE" --arg out "$OUT" --argjson plan "$PLAN_JSON" '{title:$title, out_path:$out, plan:$plan}')"

echo "— render —"
curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' -d "$RBODY" "$API/pptx/render" | jq . || true

echo "— latest + head/get —"
BN="$(curl -sS "${HDR[@]}" "$API/exports/latest" | jq -r .latest.name 2>/dev/null || true)"
if [ -n "$BN" ] && [ "$BN" != "null" ]; then
  echo "latest: $BN"
  curl -sI --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p' || true
  curl -s  --get --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download" || true
  ls -lh "/tmp/$BN" 2>/dev/null || true
else
  echo "[warn] kein Export vorhanden – Download übersprungen."
fi
