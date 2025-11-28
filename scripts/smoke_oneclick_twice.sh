#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
export API STRATGEN_API_KEY="$KEY"

echo "– run #1 (mit (RAG))"
scripts/oneclick_dedup.sh "Acme GmbH" "Go-to-Market 2026 (RAG)" "probe" >/dev/null

echo "– run #2 (ohne (RAG))"
scripts/oneclick_dedup.sh "Acme GmbH" "Go-to-Market 2026" "probe" >/dev/null

echo "– latest:"
curl -sS "$API/exports/latest" | jq -r '.latest.name'
echo "– HEAD:"
BN=$(curl -sS "$API/exports/latest" | jq -r '.latest.name')
curl -sI --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p'
