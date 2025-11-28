#!/usr/bin/env bash
# =============================================
# StratGen: Komplettes System Startup
# =============================================
# Startet alle Services und prüft Status
# =============================================

set -euo pipefail

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     StratGen: System Startup               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# 1. Verzeichnisse prüfen
# ============================================
echo -e "${YELLOW}[1/7] Prüfe Verzeichnisse...${NC}"
mkdir -p ~/stratgen/logs
mkdir -p ~/stratgen/data
mkdir -p ~/stratgen/data/exports
mkdir -p ~/stratgen/data/knowledge
mkdir -p ~/stratgen/static/images
echo -e "${GREEN}  ✓ Verzeichnisse OK${NC}"

# ============================================
# 2. Virtual Environment aktivieren
# ============================================
echo -e "${YELLOW}[2/7] Aktiviere Python venv...${NC}"
if [[ -d ~/stratgen/.venv ]]; then
    source ~/stratgen/.venv/bin/activate
    echo -e "${GREEN}  ✓ venv aktiviert: $(which python)${NC}"
else
    echo -e "${RED}  ✗ venv nicht gefunden in ~/stratgen/.venv${NC}"
    echo -e "${YELLOW}    Erstelle mit: python -m venv ~/stratgen/.venv${NC}"
fi

# ============================================
# 3. Ollama starten (LLM)
# ============================================
echo -e "${YELLOW}[3/7] Prüfe Ollama (LLM)...${NC}"
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}  ✓ Ollama läuft bereits${NC}"
else
    if command -v ollama &> /dev/null; then
        echo -e "${YELLOW}  Starte Ollama...${NC}"
        ollama serve > ~/stratgen/logs/ollama.log 2>&1 &
        sleep 2
        echo -e "${GREEN}  ✓ Ollama gestartet${NC}"
    else
        echo -e "${RED}  ✗ Ollama nicht installiert${NC}"
        echo -e "${YELLOW}    Installiere: curl -fsSL https://ollama.ai/install.sh | sh${NC}"
    fi
fi

# ============================================
# 4. Qdrant starten (Vector DB)
# ============================================
echo -e "${YELLOW}[4/7] Prüfe Qdrant (Vector DB)...${NC}"
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Qdrant läuft bereits${NC}"
else
    if command -v qdrant &> /dev/null; then
        echo -e "${YELLOW}  Starte Qdrant...${NC}"
        qdrant > ~/stratgen/logs/qdrant.log 2>&1 &
        sleep 2
        echo -e "${GREEN}  ✓ Qdrant gestartet${NC}"
    elif [[ -d ~/.qdrant ]] || [[ -d ~/stratgen/.qdrant ]]; then
        echo -e "${YELLOW}  ✗ Qdrant installiert aber nicht im PATH${NC}"
    else
        echo -e "${YELLOW}  ⚠ Qdrant nicht gefunden (optional)${NC}"
    fi
fi

# ============================================
# 5. StratGen API starten
# ============================================
echo -e "${YELLOW}[5/7] Prüfe StratGen API...${NC}"
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ StratGen API läuft bereits${NC}"
else
    echo -e "${YELLOW}  Starte StratGen API...${NC}"
    cd ~/stratgen
    if [[ -d .venv ]]; then
        source .venv/bin/activate
    fi
    nohup uvicorn backend.api:app --host 0.0.0.0 --port 8011 > ~/stratgen/logs/api.log 2>&1 &
    sleep 3
    if curl -s http://localhost:8011/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ StratGen API gestartet${NC}"
    else
        echo -e "${RED}  ✗ API Start fehlgeschlagen - siehe logs/api.log${NC}"
    fi
fi

# ============================================
# 6. Git Auto-Sync Timer
# ============================================
echo -e "${YELLOW}[6/7] Prüfe Git Auto-Sync Timer...${NC}"
if sudo systemctl is-active --quiet stratgen-sync.timer; then
    echo -e "${GREEN}  ✓ Auto-Sync Timer läuft${NC}"
else
    echo -e "${YELLOW}  Starte Auto-Sync Timer...${NC}"
    sudo systemctl start stratgen-sync.timer
    echo -e "${GREEN}  ✓ Auto-Sync Timer gestartet${NC}"
fi

# ============================================
# 7. Status-Übersicht
# ============================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     System Status                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Services prüfen
check_service() {
    if $2 > /dev/null 2>&1; then
        echo -e "  $1: ${GREEN}✓ Online${NC}"
    else
        echo -e "  $1: ${RED}✗ Offline${NC}"
    fi
}

check_service "StratGen API    (8011)" "curl -s http://localhost:8011/health"
check_service "Ollama LLM     (11434)" "curl -s http://localhost:11434/api/tags"
check_service "Qdrant DB       (6333)" "curl -s http://localhost:6333/health"

echo ""
echo -e "  Git Branch: ${BLUE}$(cd ~/stratgen && git branch --show-current)${NC}"
echo -e "  Auto-Sync:  $(sudo systemctl is-active stratgen-sync.timer 2>/dev/null || echo 'nicht installiert')"
echo ""

# ============================================
# URLs
# ============================================
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     URLs                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  API Docs:     ${GREEN}http://localhost:8011/docs${NC}"
echo -e "  Health:       ${GREEN}http://localhost:8011/health${NC}"
echo -e "  GitHub:       ${GREEN}https://github.com/danielploetz-glitch/stratgen${NC}"
echo ""
