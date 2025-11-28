#!/usr/bin/env bash
# =============================================
# StratGen: Staging → Main Merge
# =============================================
# Merged staging nach main (nur wenn Tests OK)
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     StratGen: Staging → Main Merge         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# 1. Aktuelle Branch speichern
original_branch=$(git branch --show-current)

# 2. Sicherstellen dass alles committet ist
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${YELLOW}Uncommittete Änderungen gefunden, committe zuerst...${NC}"
    git add -A
    git commit -m "auto: pre-merge sync $(date +%Y-%m-%d\ %H:%M:%S)"
    git push origin staging
fi

# 3. Neueste Änderungen holen
echo -e "${YELLOW}[1/5] Hole neueste Änderungen...${NC}"
git fetch origin

# 4. Zu main wechseln
echo -e "${YELLOW}[2/5] Wechsle zu main...${NC}"
git checkout main
git pull origin main

# 5. Staging mergen
echo -e "${YELLOW}[3/5] Merge staging → main...${NC}"
if git merge staging -m "merge: staging → main $(date +%Y-%m-%d\ %H:%M:%S)"; then
    echo -e "${GREEN}  ✓ Merge erfolgreich${NC}"
else
    echo -e "${RED}  ✗ Merge-Konflikt! Bitte manuell lösen.${NC}"
    exit 1
fi

# 6. Zu GitHub pushen
echo -e "${YELLOW}[4/5] Pushe zu main...${NC}"
git push origin main

# 7. Zurück zu staging
echo -e "${YELLOW}[5/5] Wechsle zurück zu staging...${NC}"
git checkout staging

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✓ MERGE ERFOLGREICH!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  main ist jetzt auf dem Stand von staging."
echo -e "  Prüfe auf GitHub: ${BLUE}https://github.com/danielploetz-glitch/stratgen${NC}"
echo ""
