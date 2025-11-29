#!/usr/bin/env bash
# =============================================
# Agent V3.1 Upgrade: Quick Wins + Intelligence
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Agent V3.1 Upgrade                        ║"
echo "║  Quick Wins + Agent Intelligence           ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/5] Erstelle Backup..."
cp backend/agent_v3_api.py backend/agent_v3_api.py.backup_$(date +%Y%m%d_%H%M%S)
echo "  ✓ Backup erstellt"

# 2. Neuen Agent kopieren
echo ""
echo "[2/5] Installiere Agent V3.1..."
if [[ -f ~/Downloads/agent_v3_api.py ]]; then
    cp ~/Downloads/agent_v3_api.py backend/agent_v3_api.py
    echo "  ✓ agent_v3_api.py aktualisiert"
else
    echo "  ✗ agent_v3_api.py nicht in Downloads!"
    exit 1
fi

# 3. Test Import
echo ""
echo "[3/5] Teste Import..."
source .venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
from backend.agent_v3_api import router, OLLAMA_MODELS, NLG_MODULES
print(f'  ✓ Import OK')
print(f'  ✓ Models konfiguriert: {list(OLLAMA_MODELS.keys())}')
print(f'  ✓ NLG Module geladen: {len(NLG_MODULES)}')
"

# 4. API neu starten
echo ""
echo "[4/5] Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

# 5. Test
echo ""
echo "[5/5] Teste Agent V3.1..."
sleep 3

echo ""
echo "=== Status Check ==="
curl -s http://localhost:8011/agent/v3/status | python3 -m json.tool

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Agent V3.1 Upgrade abgeschlossen!       ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Quick Win 1: NLG-Module Integration"
echo "  ✓ Quick Win 2: Template-Learner Integration"
echo "  ✓ Quick Win 3: Feedback-Loop Integration"
echo "  ✓ Quick Win 4: Multi-Model Support"
echo "  ✓ Stufe 1: Agent Intelligence"
echo "    - Analyse & Planning Phase"
echo "    - Kontextbewusste Generierung"
echo "    - Iterative Selbstverbesserung"
echo ""
echo "Test mit:"
echo '  curl -X POST http://localhost:8011/agent/run_v3 \'
echo '    -H "Content-Type: application/json" \'
echo '    -d "{\"topic\": \"KI-Strategie\", \"deck_size\": \"medium\", \"auto_improve\": true}"'
