#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"

echo "• latest"
BN="$(curl -s "$API/exports/latest" | jq -r '.latest.name // empty')"
if [ -z "$BN" ]; then
  echo "  (keine Exporte gefunden)"
  exit 0
fi

echo "• head download ($BN)"
curl -s -I --get --data-urlencode "name=$BN" "$API/exports/download" | sed -n '1,8p'

echo "• get download -> /tmp/$BN"
curl -s --get --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download"
test -f "/tmp/$BN" && ls -lh "/tmp/$BN" || { echo "download fehlgeschlagen"; exit 1; }
echo "✓ ok"
