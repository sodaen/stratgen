#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8011}"
base="http://127.0.0.1:${PORT}"

echo "[0] health"
curl -sSf "$base/pptx/health" | jq -r '.ok'

echo "[1] save project"
pid=$(curl -sSf -X POST "$base/projects/save" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"customer_name":"Acme GmbH","topic":"Demo","outline":{"title":"Demo","sections":[{"title":"One","bullets":["A","B"]}]}}' \
  | python -c 'import sys,json; j=json.load(sys.stdin); print((j.get("project") or {}).get("id") or (j.get("id") or j.get("project_id") or ""))')
[ -n "$pid" ] || { echo "ERROR: no project id returned"; exit 1; }
echo "  -> pid=$pid"

echo "[2] render pptx (template_name=master)"
curl -sSf -X POST "$base/pptx/render_from_project/$pid?template_name=master" | jq -r '.path'

echo "[3] export.md direct"
curl -sSf -X POST "$base/projects/$pid/export.md" -o /tmp/export.md
wc -c /tmp/export.md

echo "[3b] export.md alias (/export/...)"
curl -sSf -X POST "$base/export/projects/$pid/export.md" -o /tmp/export.alias.md
wc -c /tmp/export.alias.md

echo "[4] exports list"
curl -sSf "$base/exports/list" | jq '.ok,.count' 
