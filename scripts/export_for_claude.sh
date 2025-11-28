#!/usr/bin/env bash
# =============================================
# StratGen: Export für Claude
# =============================================
# Erstellt eine TXT-Datei mit allen relevanten
# Code-Dateien, die du an Claude senden kannst.
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

# Ausgabe-Datei
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/home/sodaen/stratgen/exports/claude_export_${TIMESTAMP}.txt"

mkdir -p /home/sodaen/stratgen/exports

echo "╔════════════════════════════════════════════╗"
echo "║  StratGen: Export für Claude               ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Header
cat > "$OUTPUT_FILE" << 'HEADER'
================================================================================
STRATGEN CODE EXPORT
================================================================================
Erstellt: TIMESTAMP_PLACEHOLDER
Repository: https://github.com/danielploetz-glitch/stratgen
Branch: BRANCH_PLACEHOLDER
================================================================================

HEADER

# Timestamp und Branch einfügen
sed -i "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S')/" "$OUTPUT_FILE"
sed -i "s/BRANCH_PLACEHOLDER/$(git branch --show-current)/" "$OUTPUT_FILE"

# Git Status
echo "" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "GIT STATUS" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
git status --short >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Letzte Commits
echo "================================================================================" >> "$OUTPUT_FILE"
echo "LETZTE 10 COMMITS" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
git log --oneline -10 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Datei-Liste
echo "================================================================================" >> "$OUTPUT_FILE"
echo "PROJEKT-STRUKTUR" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
find . -type f -name "*.py" \
    -not -path "./.venv/*" \
    -not -path "./.git/*" \
    -not -path "./__pycache__/*" \
    -not -name "*.bak*" \
    | sort >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Funktion zum Hinzufügen von Dateien
add_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        echo "" >> "$OUTPUT_FILE"
        echo "================================================================================" >> "$OUTPUT_FILE"
        echo "FILE: $file" >> "$OUTPUT_FILE"
        echo "================================================================================" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo "[✓] $file"
    fi
}

echo "Exportiere Dateien..."
echo ""

# ============================================
# BACKEND - Haupt-API
# ============================================
echo "--- Backend (Haupt) ---"
add_file "backend/api.py"
add_file "backend/__init__.py"

# ============================================
# BACKEND - Wichtige API-Router
# ============================================
echo "--- Backend (Router) ---"
add_file "backend/agent_api.py"
add_file "backend/agent_run_api.py"
add_file "backend/agent_run_v2_router.py"
add_file "backend/content_api.py"
add_file "backend/knowledge_api.py"
add_file "backend/knowledge_answer_api.py"
add_file "backend/pptx_api.py"
add_file "backend/projects_api.py"
add_file "backend/projects_fix_api.py"
add_file "backend/exports_api.py"
add_file "backend/providers_api.py"
add_file "backend/datasources_api.py"
add_file "backend/research_api.py"
add_file "backend/enrich_api.py"
add_file "backend/critique_api.py"
add_file "backend/personas_api.py"
add_file "backend/metrics_api.py"
add_file "backend/brief_api.py"
add_file "backend/planner_api.py"
add_file "backend/strategy_api.py"

# ============================================
# SERVICES - Business Logic
# ============================================
echo "--- Services ---"
add_file "services/__init__.py"
add_file "services/generator.py"
add_file "services/llm.py"
add_file "services/rag_pipeline.py"
add_file "services/knowledge.py"
add_file "services/datasource_store.py"
add_file "services/ds_ingest.py"
add_file "services/ppt_renderer.py"
add_file "services/deck_filler.py"
add_file "services/nlg.py"
add_file "services/critic.py"
add_file "services/reviewer.py"
add_file "services/textnorm.py"

# ============================================
# SERVICES - Providers
# ============================================
echo "--- Services/Providers ---"
add_file "services/providers/__init__.py"
add_file "services/providers/common.py"
add_file "services/providers/statista.py"
add_file "services/providers/brandwatch.py"
add_file "services/providers/talkwalker.py"

# ============================================
# SERVICES - NLG Module
# ============================================
echo "--- Services/NLG ---"
add_file "services/nlg/__init__.py"
add_file "services/nlg/gtm_basics.py"
add_file "services/nlg/personas.py"
add_file "services/nlg/competitive.py"
add_file "services/nlg/market_sizing.py"

# ============================================
# CONFIG
# ============================================
echo "--- Config ---"
add_file ".env.example"
add_file "requirements.txt"
add_file "pyproject.toml"

# ============================================
# ZUSAMMENFASSUNG
# ============================================
echo ""
echo "================================================================================" >> "$OUTPUT_FILE"
echo "ENDE DES EXPORTS" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"

# Statistik
FILE_COUNT=$(grep -c "^FILE:" "$OUTPUT_FILE" || echo "0")
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  Export abgeschlossen!                     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "  Datei    : $OUTPUT_FILE"
echo "  Dateien  : $FILE_COUNT"
echo "  Zeilen   : $LINE_COUNT"
echo "  Größe    : $SIZE"
echo ""
echo "  Kopiere diese Datei und füge sie in den Claude-Chat ein,"
echo "  oder lade sie als Datei hoch."
echo ""
