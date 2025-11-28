#!/usr/bin/env bash
set -Eeuo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
OUT="/tmp/stratgen_handover_$(date +%F-%H%M%S)"
mkdir -p "$OUT"

curl -fsS "$BASE/openapi.json" -o "$OUT/openapi.json" || true
cp -a gunicorn.conf.py "$OUT/" 2>/dev/null || true
cp -a backend "$OUT/backend" 2>/dev/null || true
cp -a scripts "$OUT/scripts" 2>/dev/null || true
mkdir -p "$OUT/systemd"
cp -a /etc/systemd/system/stratgen.service.d "$OUT/systemd/" 2>/dev/null || true

cat > "$OUT/README_HANDOVER.md" <<'MD'
# Stratgen – Handover
- Base URL: http://127.0.0.1:8011
- Default agent route: /agent/run → v2 (AGENT_DEFAULT_VERSION=2)
- Key env: APP_ENV=prod, OLLAMA_HOST, LLM_MODEL=mistral, STRATGEN_INTERNAL_URL
- Important endpoints: /agent/run_v2, /agent/review, /agent/autotune, /agent/state/*
- Services/Timers: stratgen.service, stratgen-warmup.timer, stratgen-exports-prune.timer
MD

tar -C "$(dirname "$OUT")" -czf "${OUT}.tar.gz" "$(basename "$OUT")"
echo "Bundle: ${OUT}.tar.gz"
