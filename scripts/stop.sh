#!/usr/bin/env bash
set -Eeuo pipefail
fuser -k 8000/tcp 2>/dev/null || true
pkill -f "uvicorn.*backend.api:app" 2>/dev/null || true
echo "✅ Uvicorn auf :8000 gestoppt (falls vorhanden)."
