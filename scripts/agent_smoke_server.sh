#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TOPIC="${1:-Agent end-to-end smoke}"

R=$(curl -fsS -X POST "$BASE/agent/run_v0" -H 'Content-Type: application/json' \
      -d "$(jq -n --arg t "$TOPIC" '{topic:$t,k:3,revise:true}')")

echo "$R" | jq '{ok,topic,project_id,pptx_url,export_json}'

pptx=$(jq -r '.pptx_url // empty' <<<"$R")
json=$(jq -r '.export_json // empty' <<<"$R")

if [ -n "$pptx" ]; then
  curl -fSLo "/tmp/agent_smoke.pptx" "$BASE$pptx"
  file /tmp/agent_smoke.pptx | grep -q 'PowerPoint' && echo "✅ PPTX /tmp/agent_smoke.pptx"
fi

if [ -n "$json" ]; then
  curl -fSLo "/tmp/agent_smoke.json" "$BASE$json"
  jq '{topic,project_id,snippet}' /tmp/agent_smoke.json
fi
