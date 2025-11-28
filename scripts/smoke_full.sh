#!/usr/bin/env bash
set -euo pipefail
base="${1:-http://127.0.0.1:8011}"

echo "[0] health"
curl -sSf "$base/" >/dev/null

echo "[1] save"
pid=$(curl -sSf -X POST "$base/projects/save" -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON' | jq -r '.project.id'
{"customer_name":"Acme GmbH","topic":"GTM 2026","outline":{"sections":[{"title":"Intro","bullets":["Zielbild","Roadmap"]}]}}
JSON
)
echo "pid=$pid"

echo "[2] merge brief"
curl -sSf -X POST "$base/briefs/merge_to_project?project_id=${pid}" -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON' | jq -e '.ok==true' >/dev/null
{"brief":{"goals":["Leads","Pipeline"],"constraints":["Budget"],"brand_color":"#22c55e"}}
JSON

echo "[3] personas"
pers=$(curl -sSf -X POST "$base/personas/suggest" -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"product":"B2B SaaS","countries":["DE"]}
JSON
)
echo "$pers" | jq -e '.ok==true and (.personas|type=="array")' >/dev/null

echo "[4] messaging"
matrix=$(jq -n --argjson per "$(echo "$pers" | jq '.personas')" \
  '{personas:$per, value_props:["Schneller","Günstiger","Sicherer"]}')
curl -sSf -X POST "$base/messaging/matrix" -H 'Content-Type: application/json' -d "$matrix" | jq -e '.ok==true' >/dev/null

echo "[5] metrics"
curl -sSf -X POST "$base/metrics/suggest" -H 'Content-Type: application/json' --data-binary @- <<'JSON' | jq -e '.ok==true' >/dev/null
{"goal":"Leads"}
JSON

echo "[6] media mix"
curl -sSf -X POST "$base/plans/media_mix" -H 'Content-Type: application/json' --data-binary @- <<'JSON' | jq -e '.ok==true' >/dev/null
{"budget":10000,"channels":["SEA","Paid Social","Content"]}
JSON

echo "[7] critique"
curl -sSf -X POST "$base/projects/${pid}/critique" | jq -e '.ok==true' >/dev/null

echo "[8] snapshot"
curl -sSf -X POST "$base/projects/${pid}/versions/snapshot" | jq -e '.ok==true' >/dev/null

echo "[9] render pptx (mid)"
curl -sSf -X POST "$base/pptx/render_from_project/${pid}?length=mid" | jq -e '.ok==true and (.path|length>0)'

echo "[10] latest export"
curl -sSf "$base/exports/latest?ext=pptx" | jq .
