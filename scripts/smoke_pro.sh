#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

BRIEF=$'Unternehmensbriefing: AVT Plus – KI-gestützte Postproduktion.\nUse Cases: Auto-Transkription, Smart Rough Cut, Auto-Subtitles, QC-Assist.'
PAYLOAD=$(jq -nc --arg cn "AVT Plus" --arg topic "KI in der Postproduktion (Broadcast)" --arg brief "$BRIEF" \
  '{customer_name:$cn, topic:$topic, brief:$brief, outline:{title:"Deck", sections:[{title:"Executive Summary"},{title:"Use Cases"}]}, meta:{}}')

echo "== Save =="
SAVE_JSON="$TMP/save.json"
curl --fail-with-body -sS -w '%{http_code}\n' -o "$SAVE_JSON" \
  -H 'content-type: application/json' -X POST "$BASE/projects/save" -d "$PAYLOAD" | tail -n1
PID=$(jq -r '.project.id' "$SAVE_JSON"); echo "PID=$PID"

echo "== Generate (Pro) =="
curl --fail-with-body -sS -w '%{http_code}\n' -o "$TMP/gen.json" \
  -H 'content-type: application/json' -X POST "$BASE/projects/$PID/generate" -d '{"slides":24}' | tail -n1

echo "== Render =="
RENDER_JSON="$TMP/render.json"
curl --fail-with-body -sS -w '%{http_code}\n' -o "$RENDER_JSON" \
  -X POST "$BASE/pptx/render_from_project/$PID" | tail -n1
cat "$RENDER_JSON" | jq .

URL=$(jq -r '.url // empty' "$RENDER_JSON")
JURL=$(jq -r '.json_url // empty' "$RENDER_JSON")

echo "== Assertions =="
SLIDES=$(curl -fsS "$BASE/projects/$PID" | jq -r '.project.meta.slide_plan | length')
echo "Slides: $SLIDES"; test "$SLIDES" -ge 18

HAS_COMP=$(curl -fsS "$BASE/projects/$PID" \
  | jq -r '[.project.meta.slide_plan[].title | ascii_downcase] | any(test("compliance|dsgvo"))')
echo "Compliance present: $HAS_COMP"; test "$HAS_COMP" = "true"

UC_DETAIL=$(curl -fsS "$BASE/projects/$PID" \
  | jq -r '[.project.meta.slide_plan[].title | ascii_downcase | select(startswith("use case – "))] | length')
echo "UC detail slides: $UC_DETAIL"; test "$UC_DETAIL" -ge 2

echo "== Downloads =="
if [ -n "$URL" ]; then
  curl --fail-with-body -sS -I "$BASE$URL" | head -n1 | grep -q "200" 
fi
if [ -n "$JURL" ]; then
  curl --fail-with-body -sS -I "$BASE$JURL" | head -n1 | grep -q "200"
fi
echo "OK ✅"
