#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8001}"
export ENABLE_STYLE_TEMPLATE_APIS="${ENABLE_STYLE_TEMPLATE_APIS:-1}"
exec uvicorn backend.api:app --host 127.0.0.1 --port "$PORT" --reload
