#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TITLE="${1:-AI roadmap demo}"
SECTIONS_JSON='["Intro","Plan","Next Steps"]'

PID=$(curl -fsS -X POST "$BASE/projects/save" -H 'Content-Type: application/json' \
  -d "$(jq -n --arg title "$TITLE" --argjson sections "$SECTIONS_JSON" '{title:$title, sections:$sections}')" | jq -r '.project.id')

R=$(curl -fsS -X POST "$BASE/pptx/render_from_project/$PID")
DL=$(jq -r '.url // ("/exports/download/" + (.path|split("/")|last))' <<<"$R")
OUT="/tmp/$PID.pptx"
curl -fSLo "$OUT" "$BASE$DL"
file "$OUT" | sed 's/^/-> /'
echo "OK: $OUT"
