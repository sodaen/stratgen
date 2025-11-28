#!/usr/bin/env bash
set -u
set -o pipefail
cd "$(dirname "$0")/.."
DB="${1:-data/manifest.db}"
python3 backend/services/manifest_migrate.py run || { echo "[ERR] migration failed"; exit 1; }
echo "Migration finished (DB: $DB). Please verify with sqlite3 or scripts/manifest_scan.py"
