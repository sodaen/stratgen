#!/usr/bin/env bash
# =============================================
# StratGen: Quick Export für Claude
# =============================================
# Exportiert bestimmte Dateien oder Ordner
#
# Verwendung:
#   ./export_quick.sh backend/api.py
#   ./export_quick.sh services/
#   ./export_quick.sh backend/agent*.py
# =============================================

set -euo pipefail

cd /home/sodaen/stratgen

if [[ $# -eq 0 ]]; then
    echo "Verwendung: $0 <datei_oder_ordner> [weitere...]"
    echo ""
    echo "Beispiele:"
    echo "  $0 backend/api.py"
    echo "  $0 services/"
    echo "  $0 backend/agent*.py"
    echo "  $0 backend/ services/providers/"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/home/sodaen/stratgen/exports/claude_quick_${TIMESTAMP}.txt"

mkdir -p /home/sodaen/stratgen/exports

# Header
cat > "$OUTPUT_FILE" << EOF
================================================================================
STRATGEN - QUICK EXPORT
================================================================================
Erstellt: $(date '+%Y-%m-%d %H:%M:%S')
Branch: $(git branch --show-current)
================================================================================

EOF

echo "Exportiere..."

for pattern in "$@"; do
    # Wenn es ein Ordner ist
    if [[ -d "$pattern" ]]; then
        find "$pattern" -name "*.py" -not -name "*.bak*" | while read -r file; do
            echo "" >> "$OUTPUT_FILE"
            echo "================================================================================" >> "$OUTPUT_FILE"
            echo "FILE: $file" >> "$OUTPUT_FILE"
            echo "================================================================================" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
            echo "[✓] $file"
        done
    # Wenn es ein Glob-Pattern ist
    elif compgen -G "$pattern" > /dev/null 2>&1; then
        for file in $pattern; do
            if [[ -f "$file" ]]; then
                echo "" >> "$OUTPUT_FILE"
                echo "================================================================================" >> "$OUTPUT_FILE"
                echo "FILE: $file" >> "$OUTPUT_FILE"
                echo "================================================================================" >> "$OUTPUT_FILE"
                cat "$file" >> "$OUTPUT_FILE"
                echo "[✓] $file"
            fi
        done
    # Einzelne Datei
    elif [[ -f "$pattern" ]]; then
        echo "" >> "$OUTPUT_FILE"
        echo "================================================================================" >> "$OUTPUT_FILE"
        echo "FILE: $pattern" >> "$OUTPUT_FILE"
        echo "================================================================================" >> "$OUTPUT_FILE"
        cat "$pattern" >> "$OUTPUT_FILE"
        echo "[✓] $pattern"
    else
        echo "[!] Nicht gefunden: $pattern"
    fi
done

echo ""
echo "════════════════════════════════════════════"
echo "Export: $OUTPUT_FILE"
echo "Größe:  $(du -h "$OUTPUT_FILE" | cut -f1)"
echo "════════════════════════════════════════════"
echo ""
echo "Tipp: cat $OUTPUT_FILE | xclip -selection clipboard"
echo "      (kopiert in Zwischenablage)"
