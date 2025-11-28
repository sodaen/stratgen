#!/usr/bin/env bash
# =============================================
# StratGen: Export nur GEÄNDERTE Dateien
# =============================================
# Exportiert nur Dateien die sich seit dem
# letzten Commit geändert haben.
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/home/sodaen/stratgen/exports/claude_changes_${TIMESTAMP}.txt"

mkdir -p /home/sodaen/stratgen/exports

echo "╔════════════════════════════════════════════╗"
echo "║  StratGen: Export geänderte Dateien        ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Header
cat > "$OUTPUT_FILE" << EOF
================================================================================
STRATGEN - GEÄNDERTE DATEIEN
================================================================================
Erstellt: $(date '+%Y-%m-%d %H:%M:%S')
Branch: $(git branch --show-current)
Letzter Commit: $(git log --oneline -1)
================================================================================

EOF

# Git Diff Status
echo "GEÄNDERTE DATEIEN:" >> "$OUTPUT_FILE"
echo "==================" >> "$OUTPUT_FILE"
git status --short >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Geänderte Python-Dateien finden
CHANGED_FILES=$(git status --short | grep -E "\.py$" | awk '{print $2}' | grep -v ".bak" || true)

if [[ -z "$CHANGED_FILES" ]]; then
    echo "Keine geänderten .py Dateien gefunden."
    echo "Keine geänderten .py Dateien." >> "$OUTPUT_FILE"
else
    echo "Exportiere geänderte Dateien..."
    for file in $CHANGED_FILES; do
        if [[ -f "$file" ]]; then
            echo "" >> "$OUTPUT_FILE"
            echo "================================================================================" >> "$OUTPUT_FILE"
            echo "FILE: $file" >> "$OUTPUT_FILE"
            echo "================================================================================" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
            echo "[✓] $file"
        fi
    done
fi

# Auch Diff zeigen
echo "" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "GIT DIFF (Änderungen im Detail)" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
git diff >> "$OUTPUT_FILE" 2>/dev/null || echo "(keine staged changes)" >> "$OUTPUT_FILE"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  Export abgeschlossen!                     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "  Datei: $OUTPUT_FILE"
echo "  Größe: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
