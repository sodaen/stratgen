#!/usr/bin/env bash
# =============================================
# Stufe 2: Knowledge Enhancement Installation
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Stufe 2: Knowledge Enhancement            ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/5] Erstelle Backup..."
cp backend/agent_v3_api.py backend/agent_v3_api.py.backup_$(date +%Y%m%d_%H%M%S)
echo "  ✓ Backup erstellt"

# 2. Knowledge Enhanced Service kopieren
echo ""
echo "[2/5] Installiere knowledge_enhanced.py..."
if [[ -f ~/Downloads/knowledge_enhanced.py ]]; then
    cp ~/Downloads/knowledge_enhanced.py services/knowledge_enhanced.py
    echo "  ✓ services/knowledge_enhanced.py erstellt"
else
    echo "  ✗ knowledge_enhanced.py nicht in Downloads!"
    exit 1
fi

# 3. Agent Patchen
echo ""
echo "[3/5] Patche Agent V3.1 → V3.2..."
if [[ -f ~/Downloads/patch_knowledge_enhanced.py ]]; then
    source .venv/bin/activate
    python3 ~/Downloads/patch_knowledge_enhanced.py
else
    echo "  ✗ patch_knowledge_enhanced.py nicht in Downloads!"
    exit 1
fi

# 4. Test Import
echo ""
echo "[4/5] Teste Import..."
python3 -c "
import sys
sys.path.insert(0, '.')

# Test knowledge_enhanced
from services.knowledge_enhanced import (
    multi_source_search,
    extract_facts_from_results,
    CitationManager,
    check_status
)
print('  ✓ knowledge_enhanced importiert')

status = check_status()
print(f'  ✓ Status: {status}')

# Test Agent
from backend.agent_v3_api import HAS_KNOWLEDGE_ENHANCED
print(f'  ✓ Agent HAS_KNOWLEDGE_ENHANCED: {HAS_KNOWLEDGE_ENHANCED}')
"

# 5. API neu starten
echo ""
echo "[5/5] Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Stufe 2 Installation abgeschlossen!     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Multi-Source RAG (Knowledge + Templates + Uploads)"
echo "  ✓ Fact Extraction & Verification"
echo "  ✓ Citation Management"
echo "  ✓ Query Expansion"
echo "  ✓ Context-Aware Retrieval"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
