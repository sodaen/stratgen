#!/usr/bin/env bash
set -u
set -o pipefail
API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=()
[ -n "$KEY" ] && HDR=(-H "X-API-Key: $KEY")

DIR="${1:-samples/wave1_upload_demo}"
OUT_REL="${2:-assets_tmp/wave1_bundle.zip}"

# Absoluten Zielpfad bilden (und Eltern anlegen)
OUT_ABS="$(python3 - <<'PY' "$OUT_REL"
import os,sys
p=sys.argv[1]
print(os.path.abspath(p))
PY
)"
mkdir -p "$(dirname "$OUT_ABS")"

# ZIP bauen (zip → Python-Fallback, robust)
build_zip() {
  if command -v zip >/dev/null 2>&1; then
    # im Asset-Ordner packen, aber ABS-Pfad als Ziel
    (cd "$DIR" && zip -q -r9 "$OUT_ABS" .) || return 1
  else
    return 1
  fi
}

if ! build_zip; then
  echo "[info] zip fehlgeschlagen oder nicht vorhanden → Python-Fallback"
  python3 - "$DIR" "$OUT_ABS" <<'PY'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(out), exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for root,_,files in os.walk(src):
        for f in files:
            p=os.path.join(root,f)
            z.write(p, os.path.relpath(p, src))
print(out)
PY
fi

# Kundenname aus Manifest lesen (Fallback ENV)
CN="$(jq -r '.project.customer_name // empty' "$DIR/manifest.json" 2>/dev/null || true)"
[ -z "$CN" ] && CN="${CUSTOMER_NAME:-Acme GmbH}"

echo "-> Upload: $OUT_ABS (customer_name=$CN)"
curl -sS -X POST "${HDR[@]}" \
  -F "file=@$OUT_ABS" \
  "$API/research/upload?customer_name=$(printf '%s' "$CN" | jq -sRr @uri)&embed=0" \
  | jq . || true
echo "OK."
