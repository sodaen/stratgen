#!/usr/bin/env bash
# =============================================
# Auto-Learner Installation
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Auto-Learner Installation                 ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Service kopieren
echo "[1/4] Installiere auto_learner.py..."
if [[ -f ~/Downloads/auto_learner.py ]]; then
    cp ~/Downloads/auto_learner.py services/auto_learner.py
    chmod +x services/auto_learner.py
    echo "  ✓ services/auto_learner.py erstellt"
else
    echo "  ✗ auto_learner.py nicht in Downloads!"
    exit 1
fi

# 2. Test
echo ""
echo "[2/4] Teste Auto-Learner..."
source .venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
from services.auto_learner import get_status, learn_new_files
status = get_status()
print(f'  ✓ Status: {status[\"total_learned\"]} Dateien gelernt')
print(f'  ✓ Verzeichnisse: {list(status[\"watch_directories\"].keys())}')
"

# 3. Initialer Scan
echo ""
echo "[3/4] Führe initialen Scan durch..."
python3 services/auto_learner.py scan

# 4. Systemd Service (optional)
echo ""
echo "[4/4] Systemd Service..."
if [[ -f ~/Downloads/stratgen-autolearn.service ]]; then
    echo "  Um den Daemon als Systemd-Service zu installieren:"
    echo "    sudo cp ~/Downloads/stratgen-autolearn.service /etc/systemd/system/"
    echo "    sudo systemctl daemon-reload"
    echo "    sudo systemctl enable stratgen-autolearn"
    echo "    sudo systemctl start stratgen-autolearn"
else
    echo "  Service-Datei nicht gefunden (optional)"
fi

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Auto-Learner Installation fertig!       ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Befehle:"
echo "  python3 services/auto_learner.py scan    # Manueller Scan"
echo "  python3 services/auto_learner.py status  # Status anzeigen"
echo "  python3 services/auto_learner.py list    # Gelernte Dateien"
echo "  python3 services/auto_learner.py daemon  # Daemon starten"
echo "  python3 services/auto_learner.py reset   # Alles zurücksetzen"
