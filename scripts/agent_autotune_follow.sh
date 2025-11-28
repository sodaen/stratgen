#!/usr/bin/env bash
set -Eeuo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TOPIC="${1:-AI roadmap autotune}"

R=$(curl -fsS -X POST "$BASE/agent/autotune" -H 'Content-Type: application/json' \
      -d "$(jq -n --arg t "$TOPIC" '{topic:$t,k:3,n_variants:3}')" )
echo "$R" | jq '{ok,project_id,pptx_url,variants}'
DL=$(jq -r '.pptx_url // empty' <<<"$R"); [ -n "$DL" ] && curl -fSLo /tmp/autotune.pptx "$BASE$DL" && file /tmp/autotune.pptx | grep -q PowerPoint && echo "✅"
