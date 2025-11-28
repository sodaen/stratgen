#!/usr/bin/env bash
set -euo pipefail
LC_ALL=C

ROOT="${1:-$HOME/stratgen}"
TS="$(date +%Y%m%d_%H%M)"
OUTDIR="${ROOT}/upload_stratgen_${TS}"
mkdir -p "$OUTDIR"

cd "$ROOT"

# 0) Basis-Dateien
tree -L 3 "$ROOT" > "${OUTDIR}/snapshot_tree.txt" || true
git -C "$ROOT" log --oneline -n 30 > "${OUTDIR}/git_history.txt" || true

# 1) Manifeste (PY/JSON/YAML/MD/SQLite)
find "$ROOT" -type f -name "*.py" \
  -not -path "*/.venv/*" -not -path "*/__pycache__/*" \
  -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" | sed 's#^\./##' > "${OUTDIR}/__PY_MANIFEST__.txt" || true

find "$ROOT" -type f -name "*.json" -not -path "*/.venv/*" \
  -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" > "${OUTDIR}/__JSON_MANIFEST__.txt" || true

find "$ROOT" -type f \( -name "*.yml" -o -name "*.yaml" \) -not -path "*/.venv/*" \
  -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" > "${OUTDIR}/__YAML_MANIFEST__.txt" || true

find "$ROOT" -type f -name "*.md" -not -path "*/.venv/*" \
  -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" > "${OUTDIR}/__MD_MANIFEST__.txt" || true

find "$ROOT" -type f \( -name "*.sqlite" -o -name "*.db" \) -not -path "*/.venv/*" \
  -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" > "${OUTDIR}/__SQLITE_MANIFEST__.txt" || true

# 2) Vollinhalte: PY
: > "${OUTDIR}/__ALL_PY__.txt"
cut -f1 "${OUTDIR}/__PY_MANIFEST__.txt" | while IFS=$'\t' read -r f _; do
  [ -f "$f" ] || continue
  echo -e "\n\n===== FILE START: $f =====\n" >> "${OUTDIR}/__ALL_PY__.txt"
  sed -n '1,999999p' "$f" >> "${OUTDIR}/__ALL_PY__.txt"
  echo -e "\n===== FILE END: $f =====\n" >> "${OUTDIR}/__ALL_PY__.txt"
done

# 3) Vollinhalte: JSON (pretty, mit jq falls vorhanden; große Dateien werden nicht gecrasht)
: > "${OUTDIR}/__ALL_JSON__.txt"
if command -v jq >/dev/null 2>&1; then
  awk -F'\t' '{print $1}' "${OUTDIR}/__JSON_MANIFEST__.txt" | while read -r f; do
    [ -f "$f" ] || continue
    echo -e "\n\n===== JSON START: $f =====\n" >> "${OUTDIR}/__ALL_JSON__.txt"
    # Bei extrem großen Dateien zur Sicherheit bis 5 MB "tailorable" (optional anpassen):
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    if [ "$sz" -le 5242880 ]; then
      jq -S . "$f" >> "${OUTDIR}/__ALL_JSON__.txt" 2>/dev/null || cat "$f" >> "${OUTDIR}/__ALL_JSON__.txt"
    else
      echo "[warn] ${f} ist >5MB, Rohinhalt wird 1:1 aufgenommen." >> "${OUTDIR}/__ALL_JSON__.txt"
      cat "$f" >> "${OUTDIR}/__ALL_JSON__.txt"
    fi
    echo -e "\n===== JSON END: $f =====\n" >> "${OUTDIR}/__ALL_JSON__.txt"
  done
else
  echo "[info] jq nicht gefunden – verwende raw cat" >> "${OUTDIR}/__ALL_JSON__.txt"
  awk -F'\t' '{print $1}' "${OUTDIR}/__JSON_MANIFEST__.txt" | while read -r f; do
    [ -f "$f" ] || continue
    echo -e "\n\n===== JSON START: $f =====\n" >> "${OUTDIR}/__ALL_JSON__.txt"
    cat "$f" >> "${OUTDIR}/__ALL_JSON__.txt"
    echo -e "\n===== JSON END: $f =====\n" >> "${OUTDIR}/__ALL_JSON__.txt"
  done
fi

# 4) Vollinhalte: YAML & MD (für Doku/Configs)
for kind in YAML MD; do
  target="__ALL_${kind}__.txt"
  : > "${OUTDIR}/${target}"
  manifest="${OUTDIR}/__${kind}_MANIFEST__.txt"
  [ -f "$manifest" ] || continue
  cut -f1 "$manifest" | while read -r f; do
    [ -f "$f" ] || continue
    echo -e "\n\n===== ${kind} START: $f =====\n" >> "${OUTDIR}/${target}"
    sed -n '1,999999p' "$f" >> "${OUTDIR}/${target}"
    echo -e "\n===== ${kind} END: $f =====\n" >> "${OUTDIR}/${target}"
  done
done

# 5) SQLite-Übersicht: Schema, Tabellen, Counts, Integrity
: > "${OUTDIR}/__ALL_SQLITE__.txt"
if command -v sqlite3 >/dev/null 2>&1; then
  awk -F'\t' '{print $1}' "${OUTDIR}/__SQLITE_MANIFEST__.txt" | while read -r db; do
    [ -f "$db" ] || continue
    echo -e "\n\n===== SQLITE START: $db =====" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    echo "-- size: $(stat -c%s "$db" 2>/dev/null || echo 0) bytes" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    echo "-- integrity_check:" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    sqlite3 "$db" 'PRAGMA integrity_check;' >> "${OUTDIR}/__ALL_SQLITE__.txt" 2>/dev/null || echo "[warn] integrity_check failed" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    echo -e "\n-- schema:" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    sqlite3 "$db" '.schema' >> "${OUTDIR}/__ALL_SQLITE__.txt" 2>/dev/null || true
    echo -e "\n-- tables:" >> "${OUTDIR}/__ALL_SQLITE__.txt"
    sqlite3 "$db" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1;" >> "${OUTDIR}/__ALL_SQLITE__.txt" 2>/dev/null || true
    while read -r t; do
      [ -n "$t" ] || continue
      echo -e "\n-- count($t):" >> "${OUTDIR}/__ALL_SQLITE__.txt"
      sqlite3 "$db" "SELECT COUNT(*) FROM \"$t\";" >> "${OUTDIR}/__ALL_SQLITE__.txt" 2>/dev/null || true
    done < <(sqlite3 "$db" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1;" 2>/dev/null || true)
    echo -e "===== SQLITE END: $db =====\n" >> "${OUTDIR}/__ALL_SQLITE__.txt"
  done
else
  echo "[info] sqlite3 CLI nicht gefunden – SQLite-Analyse übersprungen" >> "${OUTDIR}/__ALL_SQLITE__.txt"
fi

# 6) Exporte (PPTX) nur listen + Checksums
( find "$ROOT/data/exports" -maxdepth 2 -type f -name "*.pptx" -printf "%p\t%TY-%Tm-%Td %TH:%TM\t%k KB\n" 2>/dev/null || true ) \
  > "${OUTDIR}/__EXPORTS_MANIFEST__.txt"
if command -v md5sum >/dev/null 2>&1; then
  ( cd "$ROOT" && md5sum $(find data/exports -type f -name "*.pptx" 2>/dev/null) ) > "${OUTDIR}/__EXPORTS_CHECKSUMS__.txt" 2>/dev/null || true
fi

# 7) Zip bauen
( cd "$(dirname "$OUTDIR")" && zip -qr "$(basename "$OUTDIR").zip" "$(basename "$OUTDIR")" )
echo "[ok] Snapshot bereit: ${OUTDIR}.zip"
