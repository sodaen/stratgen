#!/usr/bin/env bash
# =============================================
# StratGen Auto-Sync zu Staging
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

# Sicherstellen dass wir auf staging sind
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "staging" ]]; then
    git checkout staging 2>/dev/null || true
fi

# Prüfen ob es Änderungen gibt
if [[ -z $(git status --porcelain) ]]; then
    echo "[$(date)] Keine Änderungen"
    exit 0
fi

# Änderungen committen
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$(date)] Änderungen gefunden, committe..."

git add -A
git commit -m "auto: sync $timestamp" || true

# Zu staging pushen
git push origin staging

echo "[$(date)] ✓ Sync abgeschlossen"
