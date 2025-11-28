#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8011}"

echo "== Stoppe Dienste (idempotent) =="
sudo systemctl stop stratgen 2>/dev/null || true

# Optional vorhandene Dependencies neu starten, wenn sie existieren:
restart_if_present() {
  local SVC="$1"
  if systemctl list-unit-files --type=service | grep -qE "^${SVC}\.service"; then
    echo "--> restart ${SVC}"
    sudo systemctl restart "${SVC}" || sudo systemctl start "${SVC}" || true
  fi
}
# Trage hier ggf. tatsächlich genutzte Services ein:
for svc in redis-server postgresql qdrant nginx; do
  restart_if_present "$svc"
done

echo "== Starte stratgen =="
sudo systemctl start stratgen

echo "== Warte auf API (OpenAPI-Ping) =="
for i in {1..30}; do
  if curl -fsS "$BASE/openapi.json" >/dev/null; then
    echo "API up ✔"; break
  fi
  sleep 1
  if [ "$i" -eq 10 ]; then
    echo "Hinweis: prüfe, ob Port 8011 blockiert ist (fallback kill)"
    if command -v fuser >/dev/null 2>&1; then sudo fuser -k 8011/tcp || true; fi
    sudo systemctl restart stratgen || true
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ API antwortet nicht – letzte Logs:" >&2
    journalctl -u stratgen -n 120 --no-pager >&2 || true
    exit 1
  fi
done

echo "== Kurz-Logs stratgen =="
journalctl -u stratgen -n 20 --no-pager || true

echo "== Preflight & Smoke =="
./scripts/preflight.sh
./scripts/smoke_e2e.sh

# Optional: Pro-Durchlauf testen, falls vorhanden
if [ -x ./scripts/smoke_pro.sh ]; then
  echo "== Pro Smoke =="
  ./scripts/smoke_pro.sh
fi

echo "== Fertig ✅ =="
