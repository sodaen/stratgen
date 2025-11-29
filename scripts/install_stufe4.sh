#!/usr/bin/env bash
# =============================================
# Stufe 4: Learning & Adaptation Installation
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Stufe 4: Learning & Adaptation            ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/6] Erstelle Backup..."
cp backend/agent_v3_api.py backend/agent_v3_api.py.backup_$(date +%Y%m%d_%H%M%S)
echo "  ✓ Backup erstellt"

# 2. Learning Service kopieren
echo ""
echo "[2/6] Installiere learning_adaptation.py..."
if [[ -f ~/Downloads/learning_adaptation.py ]]; then
    cp ~/Downloads/learning_adaptation.py services/learning_adaptation.py
    echo "  ✓ services/learning_adaptation.py erstellt"
else
    echo "  ✗ learning_adaptation.py nicht in Downloads!"
    exit 1
fi

# 3. Agent Patchen
echo ""
echo "[3/6] Patche Agent V3.3 → V3.4..."
if [[ -f ~/Downloads/patch_learning_adaptation.py ]]; then
    source .venv/bin/activate
    python3 ~/Downloads/patch_learning_adaptation.py
else
    echo "  ✗ patch_learning_adaptation.py nicht in Downloads!"
    exit 1
fi

# 4. Test Import
echo ""
echo "[4/6] Teste Import..."
python3 -c "
import sys
sys.path.insert(0, '.')

# Test learning_adaptation
from services.learning_adaptation import (
    record_feedback,
    predict_quality,
    get_merged_style,
    check_status
)
print('  ✓ learning_adaptation importiert')

status = check_status()
print(f'  ✓ Learning active: {status[\"learning_active\"]}')
print(f'  ✓ Stats: {status[\"stats\"]}')

# Test Agent
from backend.agent_v3_api import HAS_LEARNING
print(f'  ✓ Agent HAS_LEARNING: {HAS_LEARNING}')
"

# 5. Templates lernen
echo ""
echo "[5/6] Lerne aus Templates..."
python3 -c "
import sys
sys.path.insert(0, '.')
from services.learning_adaptation import learn_from_all_templates
result = learn_from_all_templates()
print(f'  ✓ Templates gelernt: {result.get(\"learned\", 0)}')
if result.get('errors'):
    print(f'  ⚠ Fehler: {len(result[\"errors\"])}')
"

# 6. API neu starten
echo ""
echo "[6/6] Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Stufe 4 Installation abgeschlossen!     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Feedback Integration"
echo "  ✓ Style Learning (aus Templates)"
echo "  ✓ Quality Prediction"
echo "  ✓ Preference Learning"
echo "  ✓ Performance Analytics"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
