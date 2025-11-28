#!/usr/bin/env bash
# =============================================
# StratGen: Produktions-Startup mit Gunicorn
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
echo -e "${BLUE}║  StratGen: PRODUKTION Startup (Gunicorn)   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# 1. Verzeichnisse
# ============================================
echo -e "${YELLOW}[1/7] Prüfe Verzeichnisse...${NC}"
mkdir -p ~/stratgen/logs
mkdir -p ~/stratgen/data/exports
mkdir -p ~/stratgen/data/knowledge
mkdir -p ~/stratgen/static/images
echo -e "${GREEN}  ✓ OK${NC}"

# ============================================
# 2. Virtual Environment
# ============================================
echo -e "${YELLOW}[2/7] Aktiviere venv...${NC}"
source /home/sodaen/stratgen/.venv/bin/activate
echo -e "${GREEN}  ✓ OK${NC}"

# ============================================
# 3. Ollama
# ============================================
echo -e "${YELLOW}[3/7] Prüfe Ollama...${NC}"
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}  ✓ Läuft${NC}"
else
    if command -v ollama &> /dev/null; then
        ollama serve > ~/stratgen/logs/ollama.log 2>&1 &
        sleep 2
        echo -e "${GREEN}  ✓ Gestartet${NC}"
    else
        echo -e "${RED}  ✗ Nicht installiert${NC}"
    fi
fi

# ============================================
# 4. Qdrant (Docker)
# ============================================
echo -e "${YELLOW}[4/7] Prüfe Qdrant...${NC}"
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Läuft${NC}"
else
    if command -v docker &> /dev/null; then
        # Prüfen ob Container existiert
        if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
            docker start qdrant > /dev/null 2>&1
        else
            docker run -d --name qdrant -p 6333:6333 -v ~/stratgen/.qdrant:/qdrant/storage qdrant/qdrant > /dev/null 2>&1
        fi
        sleep 2
        echo -e "${GREEN}  ✓ Gestartet${NC}"
    else
        echo -e "${RED}  ✗ Docker nicht verfügbar${NC}"
    fi
fi

# ============================================
# 5. StratGen API (Gunicorn - PRODUKTION)
# ============================================
echo -e "${YELLOW}[5/7] Starte StratGen API (Gunicorn)...${NC}"

# Alte Prozesse stoppen
pkill -f "gunicorn backend.api:app" 2>/dev/null || true
pkill -f "uvicorn backend.api:app" 2>/dev/null || true
sleep 1

# Gunicorn starten (4 Worker, Produktion)
cd /home/sodaen/stratgen
nohup /home/sodaen/stratgen/.venv/bin/gunicorn backend.api:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8011 \
    --timeout 120 \
    --access-logfile ~/stratgen/logs/access.log \
    --error-logfile ~/stratgen/logs/error.log \
    > ~/stratgen/logs/gunicorn.log 2>&1 &

sleep 3

if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ API läuft (Gunicorn, 4 Worker)${NC}"
else
    echo -e "${RED}  ✗ Start fehlgeschlagen - siehe logs/gunicorn.log${NC}"
fi

# ============================================
# 6. Git Auto-Sync
# ============================================
echo -e "${YELLOW}[6/7] Prüfe Git Auto-Sync...${NC}"
if sudo systemctl is-active --quiet stratgen-sync.timer 2>/dev/null; then
    echo -e "${GREEN}  ✓ Läuft${NC}"
else
    sudo systemctl start stratgen-sync.timer 2>/dev/null || echo -e "${YELLOW}  ⚠ Timer nicht konfiguriert${NC}"
fi

# ============================================
# 7. Status
# ============================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     System Status (PRODUKTION)             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Prüfungen
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo -e "  StratGen API : ${GREEN}✓ Online (Gunicorn)${NC}"
else
    echo -e "  StratGen API : ${RED}✗ Offline${NC}"
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  Ollama LLM   : ${GREEN}✓ Online${NC}"
else
    echo -e "  Ollama LLM   : ${RED}✗ Offline${NC}"
fi

if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "  Qdrant DB    : ${GREEN}✓ Online${NC}"
else
    echo -e "  Qdrant DB    : ${RED}✗ Offline${NC}"
fi

echo ""
echo -e "  Git Branch   : ${BLUE}$(git branch --show-current)${NC}"
echo -e "  Worker       : ${BLUE}4 (Gunicorn)${NC}"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     URLs                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  API Docs : ${GREEN}http://localhost:8011/docs${NC}"
echo -e "  Health   : ${GREEN}http://localhost:8011/health${NC}"
echo -e "  GitHub   : ${GREEN}https://github.com/danielploetz-glitch/stratgen${NC}"
echo ""
