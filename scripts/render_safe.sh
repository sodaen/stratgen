#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
PID="${1:-}"
[ -n "$PID" ] || { echo "usage: $0 <project_id>"; exit 2; }

# Preflight: slide_plan sicherstellen
scripts/ensure_slide_plan.py "$PID"

# Render (mittlere Länge)
curl -sSf -X POST "$BASE/pptx/render_from_project/${PID}?length=mid" | jq .
# Letztes Exportfile ausgeben
curl -sSf "$BASE/exports/latest?ext=pptx" | jq .
