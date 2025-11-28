#!/usr/bin/env bash
set -u
set -o pipefail

API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=(); [ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

mkdir -p assets_tmp

echo "— Schritt 1: PDF-Tabellen → facts"
python3 scripts/pdf_tables_to_facts.py | jq -r '.'

echo "— Schritt 2: Units normalisieren (falls vorhanden)"
[ -f scripts/facts_normalize_units.py ] && python3 scripts/facts_normalize_units.py >/dev/null || true

echo "— Schritt 3: Charts + Insights erzeugen (falls vorhanden)"
[ -f scripts/charts_generate_and_insights.py ] && python3 scripts/charts_generate_and_insights.py >/dev/null || true

echo "— Schritt 4: Semantik/Alt-Text/Fußnoten (falls vorhanden)"
[ -f scripts/semantics_enrich.py ] && python3 scripts/semantics_enrich.py >/dev/null || true

echo "— Schritt 5: Compose → Plan sichern"
comp_json="$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
  -d '{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"KPIs Q1/Q2 + Paid"}' \
  "$API/content/compose")" || comp_json="{}"

TITLE="$(printf '%s' "$comp_json" | jq -r '.title // empty')"
PLAN_JSON="$(printf '%s' "$comp_json" | jq -c '.plan // []')"
[ -z "$TITLE" ] && TITLE="Go-to-Market 2026 (RAG) – Acme GmbH"
printf '%s' "$PLAN_JSON" > assets_tmp/_plan.json

OUT="data/exports/deck-$(date +%Y%m%d-%H%M%S).pptx"
echo "— Schritt 6: Render-Body bauen"
python3 scripts/build_render_body.py --title "$TITLE" --out "$OUT" --plan-file assets_tmp/_plan.json > assets_tmp/render_body.json
echo "Render-Body:"
jq . assets_tmp/render_body.json || cat assets_tmp/render_body.json

echo "— Schritt 7: Render"
curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json' \
     -d @assets_tmp/render_body.json "$API/pptx/render" | jq -r '.'

BN="$(basename "$OUT")"
echo "— Schritt 8: Download HEAD/GET"
curl -sI --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p'
curl -s  --get --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download"
ls -lh "/tmp/$BN" || true

echo "==> Wave 2 abgeschlossen."
