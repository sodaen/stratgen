#!/usr/bin/env bash
# =============================================
# Stufe 3: Visual Intelligence Installation
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Stufe 3: Visual Intelligence              ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/5] Erstelle Backup..."
cp backend/agent_v3_api.py backend/agent_v3_api.py.backup_$(date +%Y%m%d_%H%M%S)
echo "  ✓ Backup erstellt"

# 2. Visual Intelligence Service kopieren
echo ""
echo "[2/5] Installiere visual_intelligence.py..."
if [[ -f ~/Downloads/visual_intelligence.py ]]; then
    cp ~/Downloads/visual_intelligence.py services/visual_intelligence.py
    echo "  ✓ services/visual_intelligence.py erstellt"
else
    echo "  ✗ visual_intelligence.py nicht in Downloads!"
    exit 1
fi

# 3. Agent Patchen
echo ""
echo "[3/5] Patche Agent V3.2 → V3.3..."
if [[ -f ~/Downloads/patch_visual_intelligence.py ]]; then
    source .venv/bin/activate
    python3 ~/Downloads/patch_visual_intelligence.py
else
    echo "  ✗ patch_visual_intelligence.py nicht in Downloads!"
    exit 1
fi

# 4. Test Import
echo ""
echo "[4/5] Teste Import..."
python3 -c "
import sys
sys.path.insert(0, '.')

# Test visual_intelligence
from services.visual_intelligence import (
    enhance_slide_visuals,
    generate_chart_for_slide,
    recommend_layout,
    check_status
)
print('  ✓ visual_intelligence importiert')

status = check_status()
print(f'  ✓ Charts: {status[\"supported_charts\"]}')
print(f'  ✓ Layouts: {status[\"supported_layouts\"]}')

# Test Agent
from backend.agent_v3_api import HAS_VISUAL_INTELLIGENCE
print(f'  ✓ Agent HAS_VISUAL_INTELLIGENCE: {HAS_VISUAL_INTELLIGENCE}')
"

# 5. API neu starten
echo ""
echo "[5/5] Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Stufe 3 Installation abgeschlossen!     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Smart Chart Selection (LLM-basiert)"
echo "  ✓ Auto-Data Extraction für Charts"
echo "  ✓ Image Recommendations"
echo "  ✓ Layout Optimization"
echo "  ✓ Visual Consistency"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
