#!/bin/bash
#
# STRATGEN VOLLSTÄNDIGES STARTUP SCRIPT
# Startet ALLE Services, Modelle und Komponenten
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

STRATGEN_DIR="/home/sodaen/stratgen"
LOG_DIR="$STRATGEN_DIR/logs"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN - VOLLSTÄNDIGES SYSTEM STARTUP                 ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

check_port() {
    nc -z localhost $1 2>/dev/null || curl -s --max-time 1 "http://localhost:$1" > /dev/null 2>&1
}

wait_for_port() {
    local port=$1 name=$2 max_wait=${3:-30} waited=0
    while [ $waited -lt $max_wait ]; do
        if check_port $port; then
            echo -e "  ${GREEN}✓${NC} $name bereit (Port $port)"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo -e "  ${YELLOW}⚠${NC} $name Timeout (Port $port)"
    return 1
}

echo -e "\n${BLUE}═══ PHASE 1: Basis-Services ═══${NC}"

# Redis (Snap)
echo -e "${YELLOW}→${NC} Redis..."
if pgrep -x "redis-server" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis läuft"
else
    sudo snap start redis 2>/dev/null || true
    sleep 2
fi

# Qdrant
echo -e "${YELLOW}→${NC} Qdrant..."
if check_port 6333; then
    echo -e "  ${GREEN}✓${NC} Qdrant läuft"
else
    sudo systemctl start qdrant 2>/dev/null || true
fi

# Ollama
echo -e "${YELLOW}→${NC} Ollama..."
sudo systemctl start ollama 2>/dev/null || true
wait_for_port 11434 "Ollama" 20

echo -e "\n${BLUE}═══ PHASE 2: LLM Modelle laden ═══${NC}"

for model in "mistral:latest" "moondream:latest"; do
    echo -e "${YELLOW}→${NC} Lade $model..."
    curl -s -X POST "http://localhost:11434/api/generate" \
        -d "{\"model\": \"$model\", \"prompt\": \"warmup\", \"stream\": false}" \
        --max-time 120 > /dev/null 2>&1 && \
        echo -e "  ${GREEN}✓${NC} $model geladen" || \
        echo -e "  ${YELLOW}⚠${NC} $model nicht verfügbar"
done

echo -e "\n${BLUE}═══ PHASE 3: Stratgen Services ═══${NC}"

# Celery
echo -e "${YELLOW}→${NC} Celery Workers..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Celery läuft ($(pgrep -f 'celery.*worker' | wc -l) workers)"
else
    cd "$STRATGEN_DIR"
    source .venv/bin/activate
    celery -A tasks worker --loglevel=warning \
        -Q default,llm,llm.high,analysis,generation,export \
        --concurrency=4 > "$LOG_DIR/celery.log" 2>&1 &
    sleep 3
    echo -e "  ${GREEN}✓${NC} Celery gestartet"
fi

# Backend
echo -e "${YELLOW}→${NC} Backend API..."
sudo systemctl start stratgen 2>/dev/null || true
wait_for_port 8011 "Backend" 30

# Frontend
echo -e "${YELLOW}→${NC} Frontend..."
sudo systemctl start stratgen-frontend 2>/dev/null || true
wait_for_port 3000 "Frontend" 15

# Nginx
echo -e "${YELLOW}→${NC} Nginx..."
sudo systemctl start nginx 2>/dev/null || true

echo -e "\n${BLUE}═══ PHASE 4: Verifikation ═══${NC}"

curl -s "http://localhost:8011/unified/status" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for name, info in d.get('services', {}).items():
        status = info.get('status', 'unknown')
        sym = '✓' if status == 'online' else '✗'
        print(f'  {sym} {name}: {status}')
    print(f'  Knowledge: {d.get(\"knowledge\", {}).get(\"total_chunks\", 0)} Chunks')
except:
    print('  Status nicht abrufbar')
"

echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN STARTUP ABGESCHLOSSEN                          ║"
echo "╠═══════════════════════════════════════════════════════════════════╣"
echo "║   Frontend:  http://localhost                                     ║"
echo "║   Backend:   http://localhost:8011                                ║"
echo "║   API Docs:  http://localhost:8011/docs                           ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
