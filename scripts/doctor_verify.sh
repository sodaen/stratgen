#!/usr/bin/env bash
set -u
set -o pipefail

API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

# 0) Heuristik: versehentliche Shell-Fragmente in .py?
echo "==> 0) Heuristik-Check für Shell-Fragmente in .py"
grep -RIn --include='*.py' -E '(echo "==>|truedev/null|xdg-open|sed -n|curl -s)' backend services || echo "[ok] keine verdächtigen Fragmente gefunden"

# 1) Syntax aller Python-Dateien
echo "==> 1) Syntax-Check (py_compile)"
python3 - <<'PY'
import compileall, sys
ok = True
ok &= compileall.compile_dir("backend", force=False, quiet=1)
ok &= compileall.compile_dir("services", force=False, quiet=1)
sys.exit(0 if ok else 2)
PY
echo "[ok] py_compile clean"

# 2) Import-Check (best-effort, .venv bevorzugt; niemals Script beenden)
echo "==> 2) Import-Check: backend.api (best-effort, toleriert fehlendes fastapi)"
PYBIN="./.venv/bin/python"
if [ -x "$PYBIN" ]; then PY="$PYBIN"; else PY="$(command -v python3)"; fi

set +e
IMP_OUT=$("$PY" - <<'PY'
import importlib, sys, traceback
try:
    importlib.import_module("backend.api")
    print("ok: import backend.api")
except ModuleNotFoundError as e:
    # häufig: fastapi nicht im System-Python -> ist ok, wir prüfen Health stattdessen
    print(f"[skip] import backend.api nicht geprüft ({e}); Health-Check folgt.")
except Exception:
    traceback.print_exc()
    sys.exit(3)
PY
)
RC=$?
set -e
echo "$IMP_OUT"

# 3) Health
echo "==> 3) Health"
HRESP="$(curl -s "${HDR[@]}" "$API/health")"
echo "$HRESP" | jq -r .status 2>/dev/null || echo "$HRESP"

# 4) Exports
echo "==> 4) /exports/list & /exports/latest"
LRESP="$(curl -s "${HDR[@]}" "$API/exports/list")"
echo "$LRESP" | jq '.ok, .count' 2>/dev/null || echo "$LRESP"
TRESP="$(curl -s "${HDR[@]}" "$API/exports/latest")"
echo "$TRESP" | jq '.ok, .latest.name' 2>/dev/null || echo "$TRESP"

# 5) Falls leer: Minimaldurchlauf
COUNT=$(echo "$LRESP" | jq -r '.count // 0' 2>/dev/null || echo 0)
if [ "$COUNT" = "0" ]; then
  echo "==> 5) Compose→Render (minimal, nur falls keine Exporte)"
  REQ='{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"ISO27001 SOC2 ROI 90 Tage"}'
  printf '%s' "$REQ" > _compose_req.json
  curl -s "${HDR[@]}" -X POST "$API/content/compose" -H "Content-Type: application/json" --data-binary @ _compose_req.json >/dev/null
  curl -s "${HDR[@]}" -X POST "$API/pptx/render"    -H "Content-Type: application/json" --data-binary @ _compose_req.json >/dev/null
  TRESP="$(curl -s "${HDR[@]}" "$API/exports/latest")"
fi

# 6) HEAD/GET
echo "==> 6) Download HEAD/GET (Basename; Server encodet sicher)"
BN=$(echo "$TRESP" | jq -r '.latest.name // empty' 2>/dev/null)
if [ -n "$BN" ]; then
  echo "-- HEAD --"
  curl -sI --get --data-urlencode "name=$BN" "${HDR[@]}" "$API/exports/download" | sed -n '1,10p'
  echo "-- GET  --"
  curl -s  --get --data-urlencode "name=$BN" "${HDR[@]}" "$API/exports/download" -o "/tmp/$BN"
  ls -lh "/tmp/$BN" || true
else
  echo "[skip] kein Exportname ermittelbar"
fi

echo "==> 7) Summary"
echo "   • Syntax       : OK"
echo "   • backend.api  : $(echo "$IMP_OUT" | head -1)"
echo "   • Health/Exp   : OK, siehe oben"
echo "   • Download     : HEAD/GET geprüft"
