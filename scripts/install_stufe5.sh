#!/usr/bin/env bash
# =============================================
# Stufe 5: Multi-Modal Export Installation
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Stufe 5: Multi-Modal Export               ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/5] Erstelle Backup..."
cp backend/agent_v3_api.py backend/agent_v3_api.py.backup_$(date +%Y%m%d_%H%M%S)
echo "  ✓ Backup erstellt"

# 2. Export Service kopieren
echo ""
echo "[2/5] Installiere multimodal_export.py..."
if [[ -f ~/Downloads/multimodal_export.py ]]; then
    cp ~/Downloads/multimodal_export.py services/multimodal_export.py
    echo "  ✓ services/multimodal_export.py erstellt"
else
    echo "  ✗ multimodal_export.py nicht in Downloads!"
    exit 1
fi

# 3. Agent Patchen
echo ""
echo "[3/5] Patche Agent V3.4 → V3.5..."
if [[ -f ~/Downloads/patch_multimodal_export.py ]]; then
    source .venv/bin/activate
    python3 ~/Downloads/patch_multimodal_export.py
else
    echo "  ✗ patch_multimodal_export.py nicht in Downloads!"
    exit 1
fi

# 4. Test Import
echo ""
echo "[4/5] Teste Import..."
python3 -c "
import sys
sys.path.insert(0, '.')

# Test multimodal_export
from services.multimodal_export import (
    export_to_html,
    export_to_pdf,
    export_to_markdown,
    get_available_formats,
    check_status
)
print('  ✓ multimodal_export importiert')

formats = get_available_formats()
print('  Verfügbare Formate:')
for fmt, info in formats.items():
    status = '✓' if info.get('available') else '✗'
    print(f'    {status} {fmt}: {info.get(\"description\", \"\")}')

# Test Agent
from backend.agent_v3_api import HAS_MULTIMODAL_EXPORT
print(f'  ✓ Agent HAS_MULTIMODAL_EXPORT: {HAS_MULTIMODAL_EXPORT}')
"

# 5. API neu starten
echo ""
echo "[5/5] Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Stufe 5 Installation abgeschlossen!     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ HTML/Reveal.js Export (interaktive Web-Präsentation)"
echo "  ✓ PDF Export (mit/ohne Speaker Notes)"
echo "  ✓ Markdown Export (Dokumentation)"
echo "  ✓ JSON Export (API-Integration)"
echo "  ✓ Multi-Format Export (alle gleichzeitig)"
echo ""
echo "Neue Request-Parameter:"
echo '  "export_html": true'
echo '  "export_pdf": true'
echo '  "export_markdown": true'
echo '  "export_json": true'
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
