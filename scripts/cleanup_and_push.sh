#!/usr/bin/env bash
# =============================================
# StratGen: V1/V2 Cleanup & Git Push
# =============================================
# Entfernt alte Agent-Versionen und pusht clean state
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  StratGen: Cleanup V1/V2 & Git Push        ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ============================================
# 1. BACKUP erstellen
# ============================================
echo "[1/6] Erstelle Backup..."
BACKUP_DIR="backups/pre_v3_cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Alte Agent-Dateien sichern
for f in backend/agent_run_api.py backend/agent_run_v2_router.py backend/agent_api.py; do
    if [[ -f "$f" ]]; then
        cp "$f" "$BACKUP_DIR/" 2>/dev/null || true
        echo "  → Backup: $f"
    fi
done
echo "  ✓ Backup in $BACKUP_DIR"

# ============================================
# 2. V1/V2 Router deaktivieren
# ============================================
echo ""
echo "[2/6] Deaktiviere V1/V2 Router..."

# Liste der zu entfernenden/umbenennenden Dateien
OLD_AGENTS=(
    "backend/agent_run_api.py"
    "backend/agent_run_v2_router.py"
    "backend/agent_api.py"
)

for f in "${OLD_AGENTS[@]}"; do
    if [[ -f "$f" ]]; then
        mv "$f" "${f}.disabled"
        echo "  ✓ $f → .disabled"
    else
        echo "  - $f (nicht vorhanden)"
    fi
done

# ============================================
# 3. Temporäre/Test-Dateien aufräumen
# ============================================
echo ""
echo "[3/6] Räume temporäre Dateien auf..."

# Patch-Scripts entfernen
rm -f patch_render.py 2>/dev/null && echo "  ✓ patch_render.py entfernt" || true
rm -f fix_agent_v3.sh 2>/dev/null && echo "  ✓ fix_agent_v3.sh entfernt" || true
rm -f install_agent_v3.sh 2>/dev/null && echo "  ✓ install_agent_v3.sh entfernt" || true

# __pycache__ aufräumen
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ __pycache__ bereinigt"

# .pyc Dateien
find . -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ .pyc Dateien entfernt"

# ============================================
# 4. Prüfe was übrig bleibt
# ============================================
echo ""
echo "[4/6] Aktive Agent-Router:"
ls -la backend/agent*.py 2>/dev/null | grep -v ".disabled" || echo "  (keine aktiven agent*.py außer v3)"
ls -la backend/*agent*.py 2>/dev/null | grep -v ".disabled" || true

echo ""
echo "  Aktiver Agent: backend/agent_v3_api.py"

# ============================================
# 5. Git Status & Commit
# ============================================
echo ""
echo "[5/6] Git Commit..."

# Aktiviere venv für git hooks falls nötig
source .venv/bin/activate 2>/dev/null || true

# Git Status zeigen
echo ""
echo "  Geänderte Dateien:"
git status --short

# Alle Änderungen stagen
git add -A

# Commit
echo ""
read -p "  Commit-Message [Agent V3: Cleanup V1/V2, direkter PPTX-Export]: " MSG
MSG="${MSG:-Agent V3: Cleanup V1/V2, direkter PPTX-Export}"

git commit -m "$MSG" || echo "  (Nichts zu committen oder bereits committed)"

# ============================================
# 6. Push zu GitHub
# ============================================
echo ""
echo "[6/6] Push zu GitHub..."

# Aktueller Branch
CURRENT_BRANCH=$(git branch --show-current)
echo "  Aktueller Branch: $CURRENT_BRANCH"

# Push staging
echo ""
echo "  → Push zu staging..."
git push origin staging 2>/dev/null || git push -u origin staging

# Merge zu main
echo ""
echo "  → Merge staging → main..."
git checkout main
git merge staging -m "Merge staging: Agent V3 Release"
git push origin main

# Zurück zu staging
git checkout staging

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ Cleanup & Push abgeschlossen!           ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "  GitHub: https://github.com/danielploetz-glitch/stratgen"
echo ""
echo "  Branches aktualisiert:"
echo "    • staging (development)"
echo "    • main (production)"
echo ""
echo "  Entfernte V1/V2 Router:"
for f in "${OLD_AGENTS[@]}"; do
    echo "    • $f"
done
echo ""
echo "  Aktiver Agent:"
echo "    • backend/agent_v3_api.py"
echo ""
echo "  Nächster Schritt: API neu starten"
echo "    ~/stratgen/scripts/shutdown_all.sh"
echo "    ~/stratgen/scripts/startup_prod.sh"
