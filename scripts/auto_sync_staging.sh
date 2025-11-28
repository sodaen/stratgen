#!/usr/bin/env bash
# =============================================
# StratGen Auto-Sync zu Staging
# =============================================
# Überwacht Änderungen und pusht automatisch
# zu staging (nicht zu main!)
# =============================================

set -euo pipefail

cd ~/stratgen

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Sicherstellen dass wir auf staging sind
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "staging" ]]; then
    echo -e "${YELLOW}Wechsle zu staging...${NC}"
    git checkout staging
fi

# Prüfen ob es Änderungen gibt
if [[ -z $(git status --porcelain) ]]; then
    echo -e "${GREEN}Keine Änderungen.${NC}"
    exit 0
fi

# Änderungen committen
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
echo -e "${YELLOW}Änderungen gefunden, committe...${NC}"

git add -A
git commit -m "auto: sync $timestamp" || true

# Zu staging pushen
echo -e "${YELLOW}Pushe zu staging...${NC}"
git push origin staging

echo -e "${GREEN}✓ Sync abgeschlossen: $timestamp${NC}"
