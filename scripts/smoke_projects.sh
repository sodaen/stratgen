#!/usr/bin/env bash
set -euo pipefail
API="http://127.0.0.1:8001"
HDR=(-H "Content-Type: application/json" -H "X-API-Key: dev")

echo "[1] save..."
PID=$(curl -s -X POST "$API/projects/save" "${HDR[@]}" \
  -d '{"customer_name":"Acme GmbH","topic":"Demo","outline":{"title":"Demo","subtitle":"Kurz","sections":[{"title":"One","bullets":["A","B"]}]}}' \
  | jq -r '.project.id')
echo "PID=$PID"

echo "[2] preview..."
curl -s -D - -o /tmp/proj_preview.png -X POST "$API/projects/$PID/preview" "${HDR[@]}" \
  -d '{"style":"brand","width":800,"height":450}' | sed -n '1,5p'
file /tmp/proj_preview.png | sed -n '1p'

echo "[3] export..."
curl -s -D - -o /tmp/proj_export.pptx -X POST "$API/projects/$PID/export" "${HDR[@]}" \
  -d '{"style":"brand","filename":"proj_export.pptx"}' | sed -n '1,5p'
file /tmp/proj_export.pptx | sed -n '1p'
unzip -l /tmp/proj_export.pptx | head -n 8
