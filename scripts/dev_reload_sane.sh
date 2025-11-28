#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

APP="backend.api:app"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8011}"

# Nur backend/ beobachten; bestimmte Ordner explizit ausschließen
exec uvicorn "$APP" --host "$HOST" --port "$PORT" --reload \
  --reload-dir backend \
  --reload-exclude 'scripts/*' \
  --reload-exclude 'data/*' \
  --reload-exclude 'assets_tmp/*' \
  --reload-exclude 'samples/*'
