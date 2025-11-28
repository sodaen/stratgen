#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8011}"

echo "[0] Port freiräumen"
lsof -ti :$PORT | xargs -r kill -9 || true
sleep 0.3

echo "[1] Syntaxcheck"
. .venv/bin/activate
python -m py_compile backend/*.py

echo "[2] Start"
nohup uvicorn backend.api:app --host 127.0.0.1 --port $PORT > .run_${PORT}.log 2>&1 &
PID=$!
sleep 0.3

echo "[3] Health warten"
for i in {1..30}; do
  if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null; then
    echo "OK: API erreichbar (PID=$PID)"
    exit 0
  fi
  sleep 0.2
done

echo "FEHLER: API nicht erreichbar. Log-Auszug:"
tail -n 80 .run_${PORT}.log
exit 1
