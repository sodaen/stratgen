#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"

echo "== sockets on 8011"
ss -ltnp | grep ':8011' || true
echo "== systemctl status stratgen"
systemctl status stratgen -l --no-pager || true
echo "== last 200 lines"
journalctl -u stratgen -n 200 --no-pager || true
echo "== health"
curl -fsS "$BASE/health" || true
