#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"

echo "== Bytecode aufräumen =="
find backend services -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find backend services -name '*.pyc' -delete 2>/dev/null || true

echo "== Python-Syntax prüfen =="
mapfile -t PYFILES < <(find backend services -type f -name '*.py' | sort)
[ ${#PYFILES[@]} -gt 0 ] && python3 -m py_compile "${PYFILES[@]}"

echo "== Generator-Import prüfen =="
python3 - <<'PY'
import importlib, inspect
m = importlib.import_module("services.generator")
assert hasattr(m, "generate"), "services.generator.generate() fehlt"
print("OK import services.generator:", True)
print("generate signature:", inspect.signature(m.generate))
PY

echo "== API erreichbar & Route vorhanden? =="
curl -fsS "$BASE/openapi.json" >/dev/null
ROUTE=$(curl -fsS "$BASE/openapi.json" | jq -r '.paths | keys[]' | grep '^/projects/{pid}/generate' || true)
if [ -n "$ROUTE" ]; then
  echo "OK Route: $ROUTE"
else
  echo "❌ Route fehlt"; exit 2
fi

echo "== Preflight: OK ✅"
