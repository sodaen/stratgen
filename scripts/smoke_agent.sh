#!/usr/bin/env bash
set -euo pipefail

base="${1:-http://127.0.0.1:8011}"
api_hdr=()
[ -n "${STRATGEN_API_KEY:-}" ] && api_hdr+=(-H "X-API-Key: ${STRATGEN_API_KEY}")

echo "[0] wait-for-server"
for i in {1..40}; do
  if curl -sf "${base}/" >/dev/null; then break; fi
  sleep 0.25
done
curl -sSf "${base}/" >/dev/null

echo "[1] briefs/suggest"
curl -sSf -X POST "${base}/briefs/suggest" -H 'Content-Type: application/json' \
  -d '{"customer_name":"Acme GmbH","topic":"GTM 2026","goals":["Leads"],"constraints":["Budget"]}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.questions|length)>=1' >/dev/null
echo "   -> ok"

echo "[2] projects/save"
pid=$(curl -sSf -X POST "${base}/projects/save" -H 'Content-Type: application/json' \
  -d '{"customer_name":"Acme GmbH","topic":"Demo","outline":{"sections":[{"title":"One","bullets":["A","B"]}]}}' \
  "${api_hdr[@]}" | jq -er '.project.id // .id')
echo "   -> project_id: ${pid}"

echo "[3] briefs/merge_to_project"
curl -sSf -X POST "${base}/briefs/merge_to_project?project_id=${pid}" -H 'Content-Type: application/json' \
  -d '{"brief":{"summary":"ok","goals":["Leads"],"constraints":["Budget"]}}' \
  "${api_hdr[@]}" | jq -er '.ok==true' >/dev/null
echo "   -> ok"

echo "[4] knowledge/answer"
curl -sSf -X POST "${base}/knowledge/answer" -H 'Content-Type: application/json' \
  -d '{"q":"What is our GTM focus?","k":3}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.answer|type=="string")' >/dev/null
echo "   -> ok"

echo "[5] metrics/suggest"
curl -sSf -X POST "${base}/metrics/suggest" -H 'Content-Type: application/json' \
  -d '{"objective":"Leads","horizon_weeks":12}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.plan|length)>=1' >/dev/null
echo "   -> ok"

echo "[6] plans/media_mix"
curl -sSf -X POST "${base}/plans/media_mix" -H 'Content-Type: application/json' \
  -d '{"budget_eur":15000,"objective":"Leads","countries":["DE","AT"]}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.allocation|type=="object")' >/dev/null
echo "   -> ok"

echo "[7] projects/{id}/critique"
curl -sSf -X POST "${base}/projects/${pid}/critique" \
  "${api_hdr[@]}" | jq -er '.ok==true and (.risks|length)>=1' >/dev/null
echo "   -> ok"

echo "[8] personas/suggest"
curl -sSf -X POST "${base}/personas/suggest" -H 'Content-Type: application/json' \
  -d '{"product":"B2B SaaS","countries":["DE"]}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.personas|length)>=1' >/dev/null
echo "   -> ok"

echo "[9] messaging/matrix"
curl -sSf -X POST "${base}/messaging/matrix" -H 'Content-Type: application/json' \
  -d '{"personas":[{"name":"CMO"}],"value_props":["Effizient","Nachweisbar"]}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.matrix|length)>=1' >/dev/null
echo "   -> ok"

echo "[10] roadmap/suggest"
curl -sSf -X POST "${base}/roadmap/suggest" -H 'Content-Type: application/json' \
  -d '{"horizon_weeks":16}' \
  "${api_hdr[@]}" | jq -er '.ok==true and (.phases|length)>=1' >/dev/null
echo "   -> ok"

echo "[11] versioning: zwei Snapshots + Diff"
tsA=$(curl -sSf -X POST "${base}/projects/${pid}/versions/snapshot" "${api_hdr[@]}" | jq -er '.snapshot.ts')
sleep 0.2
tsB=$(curl -sSf -X POST "${base}/projects/${pid}/versions/snapshot" "${api_hdr[@]}" | jq -er '.snapshot.ts')
curl -sSf "${base}/projects/${pid}/diff?ts_a=${tsA}&ts_b=${tsB}" \
  "${api_hdr[@]}" | jq -er '.ok==true and (.diff|type=="array")' >/dev/null
echo "   -> ok"

echo "[12] explain/why"
curl -sSf "${base}/explain/why?recommendation=Push%20SEO" \
  "${api_hdr[@]}" | jq -er '.ok==true and (.based_on|length)>=1' >/dev/null
echo "   -> ok"

echo "[DONE] smoke passed"
