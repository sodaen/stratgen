#!/usr/bin/env bash
set -Eeuo pipefail

API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

CUSTOMER="${CUSTOMER:-Acme GmbH}"
TOPIC="${TOPIC:-Go-to-Market 2026 (RAG)}"
QUERY="${QUERY:-ISO27001 SOC2 ROI 90 Tage}"

echo "— compose —"
comp_json=$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
  -d "$(jq -c -n --arg c "$CUSTOMER" --arg t "$TOPIC" --arg q "$QUERY" \
        '{customer_name:$c, topic:$t, query:$q}')" \
  "$API/content/compose")

# prüfe, dass Plan & Titel da sind
title=$(echo "$comp_json" | jq -r '.title // empty')
plan=$(echo "$comp_json" | jq -c '.plan // empty')
if [ -z "${title:-}" ] || [ -z "${plan:-}" ]; then
  echo "[err] compose lieferte keinen title/plan:" >&2
  echo "$comp_json" | jq . >&2 || echo "$comp_json" >&2
  exit 1
fi

# Output-Dateiname (nur Basename wichtig für den /exports/download)
bn="$(echo "$CUSTOMER" | tr ' /' '__')_GTM_RAG_CLI.pptx"
out="data/exports/$bn"

echo "— render —"
render_body=$(jq -c -n --arg title "$title" --arg out "$out" --argjson plan "$plan" \
               '{title:$title, out_path:$out, plan:$plan}')

r_json=$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
         -d "$render_body" "$API/pptx/render")
echo "$r_json" | jq .

ok=$(echo "$r_json" | jq -r '.ok // false')
if [ "$ok" != "true" ]; then
  echo "[err] render fehlgeschlagen (siehe oben)" >&2
  exit 2
fi

echo "— download —"
bn_dl="$bn"
curl -sI --get --data-urlencode "name=$bn_dl" "$API/exports/download" | sed -n '1,8p'
curl -s  --get --data-urlencode "name=$bn_dl" -o "/tmp/$bn_dl" "$API/exports/download"
ls -lh "/tmp/$bn_dl"
