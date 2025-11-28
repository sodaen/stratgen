#!/usr/bin/env bash
set -Eeuo pipefail
trap 'stty sane || true' EXIT
BASE="${BASE:-http://127.0.0.1:8011}"
TOPIC="${1:-AI roadmap demo}"
K="${K:-3}"

R=$(curl -fsS --max-time 120 -X POST "$BASE/agent/run_v1" -H 'Content-Type: application/json' \
      -d "$(jq -n --arg t "$TOPIC" --argjson k "$K" '{topic:$t,k:$k,revise:true,export_pptx:true}')" )
echo "$R" | jq '{ok, run_id, project_id, pptx_url, duration_s}'
RID=$(jq -r '.run_id' <<<"$R")

for i in {1..90}; do
  S=$(curl -fsS --max-time 10 "$BASE/agent/state/$RID")
  STATUS=$(jq -r '.item.status // .item.phase // "unknown"' <<<"$S")
  echo "[$i] status=$STATUS"
  [[ "$STATUS" == "done" || "$STATUS" == "error" ]] && break
  sleep 1
done

DL=$(jq -r '.item.pptx_url // empty' <<<"$S")
if [ -n "$DL" ]; then
  OUT="/tmp/${RID}.pptx"
  curl -fSLo "$OUT" "$BASE$DL"
  file "$OUT" | grep -q 'PowerPoint' && echo "✅ PPTX: $OUT"
fi
echo "$S" | jq '{topic:(.item.topic), project_id:(.item.project_id), status:(.item.status), export_json:(.item.export_json)}'
