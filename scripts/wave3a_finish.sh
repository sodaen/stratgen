#!/usr/bin/env bash
set -u
set -o pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=(); [ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

echo "— Provider-Normalisierung"
python3 scripts/providers_normalize.py | jq -r '.'

# Units & Charts & Semantik – nur ausführen, wenn vorhanden
[ -f scripts/facts_normalize_units.py ] && python3 scripts/facts_normalize_units.py >/dev/null || true
[ -f scripts/charts_generate_and_insights.py ] && python3 scripts/charts_generate_and_insights.py >/dev/null || true
[ -f scripts/semantics_enrich.py ] && python3 scripts/semantics_enrich.py >/dev/null || true

echo "— Compose"
comp_json="$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
  -d '{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"Branchen-KPIs (Statista/Talkwalker/Brandwatch) einbinden"}' \
  "$API/content/compose")" || comp_json="{}"
TITLE="$(printf '%s' "$comp_json" | jq -r '.title // "Go-to-Market 2026 (RAG) – Acme GmbH"')"
PLAN_JSON="$(printf '%s' "$comp_json" | jq -c '.plan // []')"
printf '%s' "$PLAN_JSON" > assets_tmp/_plan.json

echo "— Render-Body (v2) mit Data Highlights aus manifest.json"
python3 scripts/build_render_body.py --title "$TITLE" --plan-file assets_tmp/_plan.json > assets_tmp/render_body.json
jq . assets_tmp/render_body.json >/dev/null 2>&1 || { echo "[ERR] ungültiger Render-Body"; cat assets_tmp/render_body.json; exit 1; }

echo "— Render"
curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
     -d @assets_tmp/render_body.json "$API/pptx/render" | jq -r '.'

BN="$(basename "$(jq -r '.out_path // ""' assets_tmp/render_body.json)")"
[ -z "$BN" ] && BN="$(basename "$(jq -r '.path // ""' assets_tmp/render_body.json)")"
[ -z "$BN" ] && BN="$(basename "$(date +data/exports/deck-%Y%m%d-%H%M%S.pptx)")"

echo "— Download HEAD/GET"
curl -sI --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p'
curl -s  --get --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download"
ls -lh "/tmp/$BN" || true
echo "==> Wave 3a abgeschlossen."
