#!/bin/bash
#
# STRATGEN VOLLSTÄNDIGES STARTUP SCRIPT
# Startet ALLE Services, Modelle und Komponenten
#
# Verwendung: ./scripts/startup-all.sh
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

STRATGEN_DIR="/home/sodaen/stratgen"
LOG_DIR="$STRATGEN_DIR/logs"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN - VOLLSTÄNDIGES SYSTEM STARTUP                 ║"
echo "║                    Alle Services & Modelle                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funktion zum Prüfen ob Service läuft
check_service() {
    if systemctl is-active --quiet "$1" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 läuft bereits"
        return 0
    else
        return 1
    fi
}

# Funktion zum Starten eines Service
start_service() {
    local service=$1
    local description=$2
    
    echo -e "${YELLOW}→${NC} Starte $description..."
    
    if check_service "$service"; then
        return 0
    fi
    
    sudo systemctl start "$service" 2>/dev/null || {
        echo -e "  ${RED}✗${NC} $service konnte nicht gestartet werden"
        return 1
    }
    
    sleep 2
    
    if check_service "$service"; then
        echo -e "  ${GREEN}✓${NC} $description gestartet"
    else
        echo -e "  ${RED}✗${NC} $description Start fehlgeschlagen"
    fi
}

# Funktion zum Prüfen ob Port erreichbar
check_port() {
    local port=$1
    local name=$2
    local max_wait=${3:-30}
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if curl -s "http://localhost:$port" > /dev/null 2>&1 || \
           curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name erreichbar auf Port $port"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    
    echo -e "  ${YELLOW}⚠${NC} $name auf Port $port nicht erreichbar (Timeout)"
    return 1
}

# Funktion zum Laden eines Ollama Modells
load_model() {
    local model=$1
    local description=$2
    
    echo -e "${YELLOW}→${NC} Lade $description ($model)..."
    
    # Prüfe ob Modell existiert
    if ! curl -s "http://localhost:11434/api/tags" | grep -q "$model"; then
        echo -e "  ${YELLOW}⚠${NC} $model nicht installiert - überspringe"
        return 1
    fi
    
    # Lade Modell (kurzer Generate-Call)
    curl -s -X POST "http://localhost:11434/api/generate" \
        -d "{\"model\": \"$model\", \"prompt\": \"warmup\", \"stream\": false}" \
        --max-time 60 > /dev/null 2>&1 && {
        echo -e "  ${GREEN}✓${NC} $description geladen"
        return 0
    } || {
        echo -e "  ${YELLOW}⚠${NC} $description Laden fehlgeschlagen"
        return 1
    }
}

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 1: System-Services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# 1. Redis
start_service "redis-server" "Redis (Message Queue)"
check_port 6379 "Redis" 10 || true

# 2. Qdrant (Vector Database)
echo -e "${YELLOW}→${NC} Starte Qdrant (Vector Database)..."
if pgrep -x "qdrant" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Qdrant läuft bereits"
else
    # Qdrant als Hintergrund-Prozess starten falls kein systemd service
    if systemctl is-enabled qdrant 2>/dev/null; then
        start_service "qdrant" "Qdrant Vector DB"
    else
        cd /opt/qdrant 2>/dev/null && ./qdrant > "$LOG_DIR/qdrant.log" 2>&1 &
        sleep 3
    fi
fi
check_port 6333 "Qdrant" 15

# 3. Ollama
start_service "ollama" "Ollama (LLM Server)"
check_port 11434 "Ollama" 20

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 2: LLM Modelle laden (Warmup)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Warte bis Ollama bereit
sleep 3

# Haupt-LLM (Mistral)
load_model "mistral:latest" "Mistral (Haupt-LLM)"

# Vision Model (Moondream)
load_model "moondream:latest" "Moondream (Vision)"

# Embedding Model
echo -e "${YELLOW}→${NC} Prüfe Embedding Model..."
if curl -s "http://localhost:11434/api/tags" | grep -q "mxbai-embed-large"; then
    echo -e "  ${GREEN}✓${NC} mxbai-embed-large verfügbar"
elif curl -s "http://localhost:11434/api/tags" | grep -q "nomic-embed-text"; then
    echo -e "  ${GREEN}✓${NC} nomic-embed-text verfügbar"
else
    echo -e "  ${YELLOW}⚠${NC} Kein Embedding-Modell gefunden"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 3: Stratgen Backend${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Celery Worker
echo -e "${YELLOW}→${NC} Starte Celery Worker..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Celery Worker läuft bereits"
else
    if systemctl is-enabled stratgen-celery 2>/dev/null; then
        start_service "stratgen-celery" "Celery Worker"
    else
        cd "$STRATGEN_DIR"
        source .venv/bin/activate
        celery -A tasks worker --loglevel=info -Q default,llm,llm.high,analysis,generation,export \
            > "$LOG_DIR/celery.log" 2>&1 &
        sleep 3
        echo -e "  ${GREEN}✓${NC} Celery Worker gestartet"
    fi
fi

# Stratgen Backend API
start_service "stratgen" "Stratgen Backend API"
check_port 8011 "Backend API" 30

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 4: Stratgen Frontend${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

start_service "stratgen-frontend" "Vite Frontend Server"
check_port 3000 "Frontend" 15

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 5: Nginx Reverse Proxy${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

start_service "nginx" "Nginx Reverse Proxy"
check_port 80 "Nginx" 10

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 6: System-Verifikation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}→${NC} Führe System-Health-Check durch..."

# Health Check
HEALTH=$(curl -s "http://localhost:8011/health" 2>/dev/null || echo '{"status":"error"}')
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    echo -e "  ${GREEN}✓${NC} Backend Health Check OK"
else
    echo -e "  ${RED}✗${NC} Backend Health Check fehlgeschlagen"
fi

# Unified Status
echo -e "${YELLOW}→${NC} Prüfe Service-Status..."
curl -s "http://localhost:8011/unified/status" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    svc = d.get('services', {})
    all_online = True
    for name, info in svc.items():
        status = info.get('status', 'unknown')
        if status == 'online':
            print(f'  \033[0;32m✓\033[0m {name}: online')
        else:
            print(f'  \033[0;31m✗\033[0m {name}: {status}')
            all_online = False
    
    # Knowledge
    chunks = d.get('knowledge', {}).get('total_chunks', 0)
    print(f'  \033[0;32m✓\033[0m Knowledge: {chunks} Chunks')
    
except Exception as e:
    print(f'  \033[0;31m✗\033[0m Status-Check fehlgeschlagen: {e}')
" 2>/dev/null || echo -e "  ${RED}✗${NC} Unified Status nicht erreichbar"

# Vision Check
echo -e "${YELLOW}→${NC} Prüfe Vision (Moondream)..."
VISION_OK=$(curl -s "http://localhost:11434/api/tags" | grep -c "moondream" || echo "0")
if [ "$VISION_OK" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Moondream Vision Model verfügbar"
else
    echo -e "  ${YELLOW}⚠${NC} Moondream nicht verfügbar"
fi

echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN STARTUP ABGESCHLOSSEN                          ║"
echo "╠═══════════════════════════════════════════════════════════════════╣"
echo "║                                                                   ║"
echo "║   Frontend:  http://localhost                                     ║"
echo "║   Backend:   http://localhost:8011                                ║"
echo "║   API Docs:  http://localhost:8011/docs                           ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Zeige laufende Prozesse
echo ""
echo -e "${BLUE}Laufende Stratgen-Prozesse:${NC}"
ps aux | grep -E "stratgen|celery|qdrant|ollama" | grep -v grep | awk '{print "  " $11, $12}' | head -10

echo ""
echo -e "${BLUE}Ports:${NC}"
echo "  80   - Nginx (Frontend)"
echo "  3000 - Vite Dev Server"
echo "  8011 - Backend API"
echo "  6333 - Qdrant"
echo "  6379 - Redis"
echo "  11434 - Ollama"
