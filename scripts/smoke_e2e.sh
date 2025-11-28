#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Smoke: Save → Generate → Render =="

BRIEF=$'Unternehmensbriefing: AVT Plus – KI-gestützte Postproduktion...\nUse Cases: Auto-Transkription, Smart Rough Cut, Auto-Subtitles, QC-Assist.'

PAYLOAD=$(jq -nc \
  --arg cn "AVT Plus" \
  --arg topic "KI in der Postproduktion (Broadcast)" \
  --arg brief "$BRIEF" \
  '{
    customer_name:$cn, topic:$topic, brief:$brief,
    outline:{ title:"KI in der Postproduktion",
      sections:[
        {title:"Executive Summary"},
        {title:"ROI & Business Case"},
        {title:"Risiken & Migrationspfad"},
        {title:"Roadmap & Pilot"},
        {title:"Use Cases"}]},
    meta:{k:6}
  }')

SAVE_JSON="$TMP/save.json"
curl --fail-with-body -sS -w '%{http_code}\n' -o "$SAVE_JSON" \
  -H 'content-type: application/json' -X POST \
  "$BASE/projects/save" -d "$PAYLOAD" | tee "$TMP/save.http"

[ "$(cat "$TMP/save.http")" = "200" ]
PID=$(jq -r '.project.id' "$SAVE_JSON")
echo "PID=$PID"

GEN_JSON="$TMP/generate.json"
curl --fail-with-body -sS -w '%{http_code}\n' -o "$GEN_JSON" \
  -H 'content-type: application/json' -X POST \
  "$BASE/projects/$PID/generate" -d '{"slides":12}' | tee "$TMP/gen.http"
[ "$(cat "$TMP/gen.http")" = "200" ]
jq -r '.ok, .project.meta.slide_plan_len' "$GEN_JSON"

RENDER_JSON="$TMP/render.json"
curl --fail-with-body -sS -w '%{http_code}\n' -o "$RENDER_JSON" \
  -X POST "$BASE/pptx/render_from_project/$PID" | tee "$TMP/render.http"
[ "$(cat "$TMP/render.http")" = "200" ]
jq . "$RENDER_JSON"

URL=$(jq -r '.url // empty' "$RENDER_JSON")
if [ -n "$URL" ]; then
  OUT="$TMP/${URL##*/}"
  echo "== Download =="
  curl --fail-with-body -sS "$BASE$URL" -o "$OUT"
  ls -lh "$OUT"
fi

echo "== Smoke: OK ✅"
