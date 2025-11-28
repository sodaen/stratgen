#!/usr/bin/env bash
set -Eeuo pipefail
trap 'stty sane || true' EXIT
BASE="${BASE:-http://127.0.0.1:8011}"

OBJ="${1:-Launch AI roadmap v2}"
AUD="${2:-Tech leads & C-level}"
VOI="${3:-Confident, concise}"
CON="${4:-Use only internal sources}"

MID=$(curl -fsS -X POST "$BASE/agent/mission/start" -H 'Content-Type: application/json' \
        -d "$(jq -n --arg o "$OBJ" --arg a "$AUD" --arg v "$VOI" --arg c "$CON" \
              '{objective:$o,audience:$a,voice:$v,constraints:$c}')" | jq -r '.mission_id')

echo "mission_id=$MID"

R=$(curl -fsS -X POST "$BASE/agent/run_v2" -H 'Content-Type: application/json' \
      -d "$(jq -n --arg m "$MID" '{mission_id:$m,k:3,revise:true,export_pptx:true}')" )
echo "$R" | jq '{ok, run_id, project_id, pptx_url, duration_s}'
RID=$(jq -r '.run_id' <<<"$R")

for i in {1..90}; do
  S=$(curl -fsS "$BASE/agent/state/$RID"); ST=$(jq -r '.item.status // .item.phase // "unknown"' <<<"$S")
  echo "[$i] status=$ST"
  [[ "$ST" == "done" || "$ST" == "error" ]] && break
  sleep 1
done

DL=$(jq -r '.item.pptx_url // empty' <<<"$S")
if [ -n "$DL" ]; then
  OUT="/tmp/${RID}.pptx"; curl -fSLo "$OUT" "$BASE$DL"
  file "$OUT" | grep -q 'PowerPoint' && echo "✅ PPTX: $OUT"
fi
echo "$S" | jq '{topic:(.item.topic), project_id:(.item.project_id), status:(.item.status), export_json:(.item.export_json)}'
