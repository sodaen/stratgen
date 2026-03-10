#!/bin/bash
# =============================================================================
# export_context.sh — stratgen Projekt-Snapshot für Claude
# Sammelt alle relevanten Dateien mit Trennern in eine Datei
# =============================================================================

OUTPUT="context_snapshot.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Dateitypen die eingesammelt werden
INCLUDE_EXTENSIONS=("py" "toml" "cfg" "ini" "yaml" "yml" "json" "sh" "md" "txt" "env.example")

# Ordner die ignoriert werden
EXCLUDE_DIRS=(".venv" "venv" "__pycache__" "node_modules" ".git" ".qdrant" "qdrant_storage" "exports" "runs" ".mypy_cache" ".pytest_cache")

# Dateien die ignoriert werden
EXCLUDE_FILES=("CHANGELOG.md" "CHANGELOG.001.md" "context_snapshot.txt" "package-lock.json" "uv.lock")

echo "==============================================================================" > "$OUTPUT"
echo "  STRATGEN PROJEKT-SNAPSHOT" >> "$OUTPUT"
echo "  Erstellt: $TIMESTAMP" >> "$OUTPUT"
echo "  Branch: $(git branch --show-current 2>/dev/null || echo 'unbekannt')" >> "$OUTPUT"
echo "  Letzter Commit: $(git log --oneline -1 2>/dev/null || echo 'unbekannt')" >> "$OUTPUT"
echo "==============================================================================" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Projektstruktur
echo "##############################################################################" >> "$OUTPUT"
echo "# PROJEKTSTRUKTUR" >> "$OUTPUT"
echo "##############################################################################" >> "$OUTPUT"
tree -I "$(IFS='|'; echo "${EXCLUDE_DIRS[*]}")" --dirsfirst -a 2>/dev/null || find . -not -path '*/.git/*' -not -path '*/.venv/*' -not -path '*/__pycache__/*' | sort
echo "" >> "$OUTPUT"

# Exclude-Pattern für find bauen
PRUNE_EXPR=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    PRUNE_EXPR="$PRUNE_EXPR -path './$dir' -prune -o"
done

# Dateien sammeln
FILE_COUNT=0

# Extension-Pattern für find
EXT_PATTERN=""
for ext in "${INCLUDE_EXTENSIONS[@]}"; do
    if [ -z "$EXT_PATTERN" ]; then
        EXT_PATTERN="-name '*.$ext'"
    else
        EXT_PATTERN="$EXT_PATTERN -o -name '*.$ext'"
    fi
done

# Alle passenden Dateien finden und einsammeln
while IFS= read -r -d '' file; do
    # Dateiname extrahieren
    basename_file=$(basename "$file")
    
    # Ausgeschlossene Dateien überspringen
    skip=false
    for excl in "${EXCLUDE_FILES[@]}"; do
        if [ "$basename_file" == "$excl" ]; then
            skip=true
            break
        fi
    done
    $skip && continue

    # Binärdateien überspringen
    if file "$file" | grep -qE "binary|executable|ELF|archive"; then
        continue
    fi

    echo "##############################################################################" >> "$OUTPUT"
    echo "# FILE: $file" >> "$OUTPUT"
    echo "##############################################################################" >> "$OUTPUT"
    cat "$file" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    
    FILE_COUNT=$((FILE_COUNT + 1))

done < <(eval "find . $PRUNE_EXPR \( $EXT_PATTERN \) -type f -print0 2>/dev/null" | sort -z)

# Zusammenfassung
echo "##############################################################################" >> "$OUTPUT"
echo "# SNAPSHOT ENDE — $FILE_COUNT Dateien exportiert" >> "$OUTPUT"
echo "##############################################################################" >> "$OUTPUT"

# Dateigröße
SIZE=$(du -sh "$OUTPUT" | cut -f1)
LINES=$(wc -l < "$OUTPUT")

echo ""
echo "✅ Snapshot erstellt: $OUTPUT"
echo "   Dateien:  $FILE_COUNT"
echo "   Zeilen:   $LINES"
echo "   Größe:    $SIZE"
echo ""
echo "👉 Inhalt teilen mit:"
echo "   cat $OUTPUT | xclip -selection clipboard   # in Zwischenablage"
echo "   cat $OUTPUT                                 # direkt ausgeben"
