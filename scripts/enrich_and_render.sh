#!/usr/bin/env bash
set -euo pipefail
base="${1:-http://127.0.0.1:8011}"
pid="${2:-}"
[ -n "$pid" ] || { echo "usage: $0 <base> <project_id>"; exit 1; }

pj_path="data/projects/${pid}/project.json"
[ -f "$pj_path" ] || { echo "not found: $pj_path"; exit 1; }

# 1) personas
pers=$(curl -sSf -X POST "$base/personas/suggest" -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"product":"B2B SaaS","countries":["DE"]}
JSON
)

# 2) messaging mit personas
matrix=$(jq -n --argjson per "$(echo "$pers" | jq '.personas')" \
  '{personas: $per, value_props:["Schneller","Günstiger","Sicherer"]}')
msg=$(curl -sSf -X POST "$base/messaging/matrix" -H 'Content-Type: application/json' -d "$matrix")

# 3) KPIs + Mix
kpis=$(curl -sSf -X POST "$base/metrics/suggest" -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"objective":"Leads","horizon_weeks":12}
JSON
)
mix=$(curl -sSf -X POST "$base/plans/media_mix" -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"budget_eur":15000,"objective":"Leads","countries":["DE","AT"]}
JSON
)

# 4) (Optional) Heuristische Knowledge-Antwort ins Projekt
know=$(curl -sSf -X POST "$base/knowledge/answer" -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"q":"What is our GTM focus?","k":3}
JSON
)

# 5) MERGE ins project.json
tmp="$(mktemp)"
jq \
  --argjson personas "$(echo "$pers" | jq '.personas')" \
  --argjson matrix   "$(echo "$msg"  | jq '.matrix')" \
  --argjson plan     "$(echo "$kpis" | jq '.plan')" \
  --argjson mix      "$(echo "$mix"  | jq '.')" \
  --argjson know     "$(echo "$know" | jq '.')" \
  '. + { personas: $personas, messaging: $matrix, metrics_plan: $plan, media_mix: $mix, knowledge: $know }' \
  "$pj_path" > "$tmp"
mv "$tmp" "$pj_path"

# 6) Snapshot + Render
curl -sSf -X POST "$base/projects/${pid}/versions/snapshot" >/dev/null
curl -sSf -X POST "$base/pptx/render_from_project/${pid}?length=mid" | jq .
