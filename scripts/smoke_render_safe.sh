#!/usr/bin/env bash
set -u  # kein -e/-o pipefail -> tolerant gegenüber jq/HTTP-Fehlern

API="${API:-http://127.0.0.1:8011}"
CUSTOMER="${CUSTOMER:-Acme GmbH}"
TOPIC="${TOPIC:-Go-to-Market 2026 (RAG)}"
QUERY="${QUERY:-}"

# Helper laden
source "$(dirname "$0")/http_helpers.sh"

echo "— health —"
if get_json "$API/health" >/dev/null; then echo "ok"; else echo "fail"; fi

echo "— compose —"
payload=$(jq -n --arg c "$CUSTOMER" --arg t "$TOPIC" --arg q "$QUERY" \
  '{customer_name:$c, topic:$t, query:$q}')
resp=$(post_json "$API/content/compose" "$payload")
# Zeige .ok/.title wenn JSON, sonst Rohantwort
echo "$resp" | jq -r '.ok, .title' 2>/dev/null || printf "%s\n" "$resp"

echo "— render (JSON header + {}) —"
r=$(post_json "$API/pptx/render" '{}')
echo "$r" | jq -r '.ok, .path' 2>/dev/null || printf "[raw] %s\n" "$r"

echo "— latest + HEAD/GET —"
bn=$(get_json "$API/exports/latest" | jq -r '.latest.name // empty' 2>/dev/null)
if [ -n "${bn:-}" ]; then
  echo "latest: $bn"
  echo "HEAD:"
  head_download "$bn" | sed -n '1,8p'
  echo
  echo "GET:"
  get_download "$bn" >/dev/null
else
  echo "[skip] kein Export vorhanden."
fi
