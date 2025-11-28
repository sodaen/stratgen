#!/usr/bin/env bash
set -euo pipefail
echo "== Preflight =="; ./scripts/preflight.sh
echo "== Pro Smoke =="; ./scripts/smoke_pro.sh
echo "== Preview Probe =="; ./scripts/preview_probe.sh
echo "== Knowledge Probe =="; ./scripts/knowledge_probe.sh
echo "== OK ✅ =="
