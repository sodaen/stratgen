#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

# 1) venv sicher da
if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi

# 2) aktivieren & Dependencies
source .venv/bin/activate
python -m pip -q install --upgrade pip wheel
if [[ -f requirements.txt ]]; then
  pip -q install -r requirements.txt
else
  # Minimal-Stack, falls keine requirements.txt vorhanden
  pip -q install fastapi "uvicorn[standard]" pydantic httpx qdrant-client python-pptx sentence-transformers
fi

# 3) Projekt importierbar machen
export PYTHONPATH="$ROOT"

# 4) Port freiräumen, falls belegt
if command -v lsof >/dev/null 2>&1 && lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "⚠️ Port 8000 belegt — beende Prozess…"
  fuser -k 8000/tcp || true
fi

# 5) Start
exec python -m uvicorn backend.api:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" --reload
