#!/usr/bin/env bash
# =============================================
# StratGen: Agent V3 Installation & Cleanup
# =============================================
# Installiert Agent V3 und entfernt V1/V2
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  StratGen: Agent V3 Installation           ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ============================================
# 1. Agent V3 kopieren
# ============================================
echo "[1/4] Kopiere Agent V3..."
if [[ -f ~/Downloads/agent_v3.py ]]; then
    cp ~/Downloads/agent_v3.py ~/stratgen/backend/agent_v3.py
    echo "  ✓ agent_v3.py kopiert"
else
    echo "  ✗ agent_v3.py nicht in Downloads gefunden!"
    echo "    Bitte erst herunterladen"
    exit 1
fi

# ============================================
# 2. api.py updaten (V3 registrieren)
# ============================================
echo ""
echo "[2/4] Registriere Agent V3 in api.py..."

# Prüfe ob V3 bereits registriert
if grep -q "agent_v3" backend/api.py; then
    echo "  ✓ Agent V3 bereits registriert"
else
    # Füge Import hinzu (nach anderen agent imports)
    # Dies ist ein einfacher Ansatz - bei komplexerer api.py ggf. manuell
    echo "  → Füge Import hinzu..."
    
    # Erstelle Backup
    cp backend/api.py backend/api.py.backup_before_v3
    
    # Hinweis: Manuelles Hinzufügen empfohlen
    echo ""
    echo "  ════════════════════════════════════════════"
    echo "  HINWEIS: Füge folgende Zeile in backend/api.py ein:"
    echo ""
    echo "  Nach den anderen Router-Imports:"
    echo "    from backend.agent_v3 import router as agent_v3_router"
    echo ""
    echo "  In der Router-Registrierung:"
    echo "    app.include_router(agent_v3_router)"
    echo "  ════════════════════════════════════════════"
fi

# ============================================
# 3. Alte Agents optional deaktivieren
# ============================================
echo ""
echo "[3/4] V1/V2 Cleanup (optional)..."
echo ""
echo "  Die alten Agent-Versionen können deaktiviert werden:"
echo "  - backend/agent_run_api.py (V1)"
echo "  - backend/agent_run_v2_router.py (V2)"
echo ""
echo "  Empfehlung: Erst V3 testen, dann V1/V2 entfernen."
echo ""
read -p "  Sollen V1/V2 jetzt umbenannt werden? (j/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Jj]$ ]]; then
    if [[ -f backend/agent_run_api.py ]]; then
        mv backend/agent_run_api.py backend/agent_run_api.py.disabled
        echo "  ✓ agent_run_api.py → .disabled"
    fi
    if [[ -f backend/agent_run_v2_router.py ]]; then
        mv backend/agent_run_v2_router.py backend/agent_run_v2_router.py.disabled
        echo "  ✓ agent_run_v2_router.py → .disabled"
    fi
else
    echo "  → V1/V2 bleiben aktiv"
fi

# ============================================
# 4. Test
# ============================================
echo ""
echo "[4/4] Test..."

# Aktiviere venv
source .venv/bin/activate

# Syntax-Check
python -c "from backend.agent_v3 import router; print('✓ Agent V3 Import OK')" 2>/dev/null || echo "✗ Import-Fehler - prüfe Dependencies"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  Installation abgeschlossen!               ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "  Nächste Schritte:"
echo "  1. API neu starten: ~/stratgen/scripts/shutdown_all.sh && ~/stratgen/scripts/startup_prod.sh"
echo "  2. Testen: curl http://localhost:8011/agent/v3/status"
echo "  3. Run: curl -X POST http://localhost:8011/agent/run_v3 -H 'Content-Type: application/json' -d '{\"topic\": \"Test\"}'"
echo ""
