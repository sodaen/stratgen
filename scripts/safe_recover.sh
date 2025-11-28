#!/usr/bin/env bash
set -u
set -o pipefail

ROOT="$HOME/stratgen"
LOG="/tmp/uvicorn_no_reload.log"
TRACE="/tmp/backend_import_traceback.log"
PYCOMPILE="/tmp/backend_pycompile.log"

cd "$ROOT" || { echo "[ERR] cannot cd $ROOT"; exit 1; }

echo "[STEP] Stoppe alle uvicorn Prozesse (safe)"
pkill -f uvicorn || true
sleep 1

echo "[STEP] Entferne alte Logs falls vorhanden"
rm -f "$LOG" "$TRACE" "$PYCOMPILE"

echo "[STEP] Prüfe Git-Status (nur informativ)"
if [ -d .git ]; then
  git --no-pager status --porcelain
  echo "Branch: $(git branch --show-current 2>/dev/null || echo '(no branch)')"
  echo "Letzte commits:"
  git --no-pager log --oneline -n 5 || true
else
  echo "[WARN] Kein .git Verzeichnis in $PWD"
fi

echo "[STEP] Versuche 'import backend.api' in Python und schreibe Traceback -> $TRACE"
python3 - <<'PY' > "$TRACE" 2>&1
import traceback
try:
    import backend.api as m
    print("OK: backend.api importiert:", m)
except Exception:
    traceback.print_exc()
PY
echo "[INFO] Import-Trace written to $TRACE"
sed -n '1,240p' "$TRACE" || true

echo "[STEP] Py-compile check (backend/*.py + backend/**/*.py) -> $PYCOMPILE"
python3 -m py_compile backend/*.py 2> "$PYCOMPILE" || true
# recurse into subdirs
find backend -name '*.py' -type f -print0 | xargs -0 -n 100 python3 -m py_compile 2>>"$PYCOMPILE" || true
echo "[INFO] py_compile output:"
sed -n '1,240p' "$PYCOMPILE" || true

echo "[STEP] Starte uvicorn ohne --reload (stdin ignored); log -> $LOG"
nohup uvicorn backend.api:app --host 127.0.0.1 --port 8011 > "$LOG" 2>&1 &
sleep 1

echo "[STEP] Warte kurz und prüfe Health"
sleep 1
curl -sS http://127.0.0.1:8011/health || true

echo "[INFO] Letzte 200 Zeilen uvicorn log:"
tail -n 200 "$LOG" || true

echo
echo "[DONE] Schau dir $TRACE und $PYCOMPILE an. Wenn Import-Error vorhanden, poste die relevanten Abschnitte hier."
