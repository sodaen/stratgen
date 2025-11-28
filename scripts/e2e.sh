#!/usr/bin/env bash
set -Eeuo pipefail
trap 'code=$?; echo; echo "❌ Fehler in Zeile $LINENO (Exit $code)"; exit $code' ERR

BASE="http://127.0.0.1:8000"
CUSTOMER="Acme GmbH"
PROJECT="Q4 Strategy"
SCOPE="Marketingstrategie & Social Media"
MARKET="Elektronikhandel"
REGION="DACH"
MIN_SLIDES=12    # >= 10

echo "[1] API erreichbar?"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/openapi.json")
[[ "$HTTP" == "200" ]] || { echo "❌ openapi.json HTTP_$HTTP"; exit 1; }
echo "  OK"

echo "[2] Brand setzen"
curl -s -X POST "$BASE/brand/set" \
  -H "Content-Type: application/json" \
  -d "{\"customer_name\":\"$CUSTOMER\",\"primary\":\"#0B5FFF\",\"secondary\":\"#111827\",\"accent\":\"#22C55E\",\"logo_path\":\"\"}" \
  | jq .

echo "[3] Outline vorschlagen"
OUTLINE_RAW="/tmp/outline_raw.json"
curl -s -X POST "$BASE/outline/suggest" \
  -H "Content-Type: application/json" \
  -d "{\"customer_name\":\"$CUSTOMER\",\"project_title\":\"$PROJECT\",\"scope\":\"$SCOPE\",\"market\":\"$MARKET\",\"region\":\"$REGION\",\"min_slides\":$MIN_SLIDES}" \
  | tee "$OUTLINE_RAW" >/dev/null

AGENDA_LEN=$(jq '.agenda | length' "$OUTLINE_RAW")
echo "  Agenda-Länge: $AGENDA_LEN"
[[ "${AGENDA_LEN:-0}" -gt 0 ]] || { echo "❌ Outline leer:"; cat "$OUTLINE_RAW"; exit 1; }

echo "[4] Outline speichern"
jq -n \
  --arg customer "$CUSTOMER" \
  --arg project "$PROJECT" \
  --argjson agenda "$(jq -c '.agenda' "$OUTLINE_RAW")" \
  '{ customer_name:$customer, project_title:$project, agenda:( $agenda | map({topic, subtopics}) ) }' \
| curl -s -X POST "$BASE/outline/save" -H "Content-Type: application/json" --data-binary @- | jq .

echo "[5] Outline auf min_slides sicherstellen ($MIN_SLIDES)"
curl -s -X POST "$BASE/outline/ensure" \
  -H "Content-Type: application/json" \
  -d "{\"customer_name\":\"$CUSTOMER\",\"project_title\":\"$PROJECT\",\"min_slides\":$MIN_SLIDES}" | jq .

# --- NEUER SCHRITT [6] ---
echo "[6] Preview (erstes Topic/Subtopic)"

TOPIC=$(jq -r '.agenda[0].topic' "$OUTLINE_RAW")
SUB=$(jq -r '.agenda[0].subtopics[0] // empty' "$OUTLINE_RAW")

jq -n \
  --arg c "$CUSTOMER" \
  --arg t "$TOPIC" \
  --arg s "$SUB" \
  --arg scope "$SCOPE" \
  --arg market "$MARKET" \
  --arg region "$REGION" \
  --argjson agenda "$(jq -c '.agenda' "$OUTLINE_RAW")" '
  { customer_name:$c,
    topic:$t,
    mode:"facts",
    brief:{scope:$scope,market:$market,region:$region},
    agenda:$agenda
  }
  | if ($s|length)>0 then .subtopic=$s else . end
' > /tmp/preview_req.json

HTTP=$(curl -s -o /tmp/preview_resp.json -w "HTTP_%{http_code}\n" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/preview_req.json \
  "$BASE/content/preview")

if [[ "$HTTP" != "HTTP_200" ]]; then
  echo "❌ Preview schlug fehl: $HTTP"
  echo "--- Antwort (gekürzt) ---"
  head -c 600 /tmp/preview_resp.json; echo
  exit 1
fi

jq '{ok, bullets:(.bullets[:3]), error}' /tmp/preview_resp.json


echo
echo "✅ E2E ok."
