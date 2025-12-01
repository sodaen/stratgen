#!/usr/bin/env bash
# =============================================
# Feature Integration Installation
# =============================================
# Installiert den Feature Orchestrator und
# integriert alle Features in den Agent V3

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Feature Integration Installation                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/5] Erstelle Backup..."
BACKUP_DIR="backups/integration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp backend/agent_v3_api.py "$BACKUP_DIR/"
echo "  ✓ Backup erstellt"

# 2. Files installieren
echo ""
echo "[2/5] Installiere Integration Services..."

cp ~/Downloads/feature_orchestrator.py services/
cp ~/Downloads/orchestrator_api.py backend/
cp ~/Downloads/patch_agent_v3_integration.py scripts/

echo "  ✓ feature_orchestrator.py"
echo "  ✓ orchestrator_api.py"
echo "  ✓ patch_agent_v3_integration.py"

# 3. Test Import
echo ""
echo "[3/5] Teste Imports..."
source .venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
from services.feature_orchestrator import orchestrator, check_status
status = check_status()
print(f'  ✓ Orchestrator: {status[\"features_available\"]}/{status[\"features_total\"]} Features')
"

# 4. Patch Agent
echo ""
echo "[4/5] Patche Agent V3..."
python3 scripts/patch_agent_v3_integration.py

# 5. API neu starten
echo ""
echo "[5/5] Starte API neu..."
pkill -f gunicorn || true
sleep 2

nohup .venv/bin/gunicorn backend.api:app \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8011 \
    --timeout 300 \
    > logs/gunicorn.log 2>&1 &

sleep 5

if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "  ✓ API läuft"
else
    echo "  ⚠ API nicht erreichbar - prüfe logs/gunicorn.log"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Feature Integration abgeschlossen!                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Neue Endpoints:"
echo "  GET  /orchestrator/status   - Orchestrator Status"
echo "  POST /orchestrator/analyze  - Orchestrierte Analyse"
echo "  POST /orchestrator/qa       - Qualitätsprüfung"
echo "  POST /orchestrator/full-pipeline - Vollständige Pipeline"
echo "  GET  /orchestrator/features - Feature-Liste"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/orchestrator/status | python3 -m json.tool'
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
