#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo "[ERR] line $LINENO failed" >&2' ERR
cd "$(dirname "$0")/.."

API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"
declare -a HDR=(); [ -n "${KEY:-}" ] && HDR=(-H "X-API-Key: $KEY")

note(){ echo -e "\n==> $*"; }
need(){ command -v "$1" >/dev/null 2>&1 || { echo "[ERR] $1 fehlt"; exit 1; }; }

need curl; need jq

note "Health"
curl -sS "$API/health" || true

note "Compose → Basisplan holen"
comp_json="$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json'   -d '{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"Bilder-Test"}'   "$API/content/compose")"

echo "$comp_json" > /tmp/image_smoke_compose.json
TITLE="$(printf '%s' "$comp_json" | jq -r '.title // empty' || true)"
BASE_PLAN="$(printf '%s' "$comp_json" | jq -c '.plan // []' || echo '[]')"
[ -n "$TITLE" ] || { echo "[ERR] compose ohne title"; jq . /tmp/image_smoke_compose.json || cat /tmp/image_smoke_compose.json; exit 1; }

note "Prüfe Bilder im samples/ (hero-bild-kampagne.jpg, key-visual.jpg)"
missing=0
for f in samples/hero-bild-kampagne.jpg samples/key-visual.jpg; do
  if [ ! -f "$f" ]; then echo "[ERR] fehlt: $f"; missing=1; fi
done
[ "$missing" -eq 0 ] || exit 1

note "Manifest ggf. ergänzen und Bild-Metadaten schreiben"
MANIFEST_SCAN_EXTRA="samples" python3 scripts/manifest_scan.py || true
python3 scripts/image_meta_index.py samples || true

note "Bild-Metadaten aus manifest.json lesen (mit Fallback)"
get_field(){ local fname="$1" field="$2";
  jq -r --arg f "$fname" --arg fld "$field"      '.assets[]? | select(.path|endswith($f)) | .[$fld] // empty' data/manifest.json | head -n1; }

HP="$(get_field 'hero-bild-kampagne.jpg' 'path')"; [ -n "$HP" ] || HP="samples/hero-bild-kampagne.jpg"
HO="$(get_field 'hero-bild-kampagne.jpg' 'orientation')"; [ -n "$HO" ] || HO="-"
HC="$(get_field 'hero-bild-kampagne.jpg' 'crop_hint')";   [ -n "$HC" ] || HC="-"

KP="$(get_field 'key-visual.jpg' 'path')"; [ -n "$KP" ] || KP="samples/key-visual.jpg"
KO="$(get_field 'key-visual.jpg' 'orientation')"; [ -n "$KO" ] || KO="-"
KC="$(get_field 'key-visual.jpg' 'crop_hint')";   [ -n "$KC" ] || KC="-"

echo "Hero  : $HP | orient=$HO | crop=$HC"
echo "KeyVis: $KP | orient=$KO | crop=$KC"

note "Platzhalter-Blöcke zusammenbauen"
EXTRA_BLOCKS="$(jq -n   --arg hp "$HP" --arg ho "$HO" --arg hc "$HC"   --arg kp "$KP" --arg ko "$KO" --arg kc "$KC" '[
  {
    "kind": "insights",
    "layout_hint": "Title and Content",
    "title": "Hero Visual – Platzhalter",
    "bullets": [
      ("Bildpfad: " + $hp),
      ("Orientierung: " + $ho),
      ("Crop-Hint: " + $hc),
      "Aktion: Vollbild (Full-bleed)"
    ]
  },
  {
    "kind": "insights",
    "layout_hint": "Title and Content",
    "title": "Key Visual – Platzhalter",
    "bullets": [
      ("Bildpfad: " + $kp),
      ("Orientierung: " + $ko),
      ("Crop-Hint: " + $kc),
      "Aktion: Side-by-Side (Content)"
    ]
  }
]')"

FINAL_PLAN="$(jq -c --argjson base "$BASE_PLAN" --argjson extra "$EXTRA_BLOCKS" '$base + $extra')"

note "Render-Body schreiben"
mkdir -p assets_tmp
OUT="data/exports/deck-$(date +%Y%m%d-%H%M%S)-images-demo.pptx"
jq -n --arg title "$TITLE" --arg out "$OUT" --argjson plan "$FINAL_PLAN"   '{title:$title, out_path:$out, plan:$plan}' > assets_tmp/render_body_images_demo.json
jq '.' assets_tmp/render_body_images_demo.json | sed 's/^/  /'

note "Render aufrufen"
resp="$(curl -sS -X POST "${HDR[@]}" -H 'Content-Type: application/json'             -d @assets_tmp/render_body_images_demo.json "$API/pptx/render")"
echo "$resp" > /tmp/render_resp_images.json
jq '.' /tmp/render_resp_images.json || cat /tmp/render_resp_images.json

BN="$(jq -r '.path | split("/")[-1] // empty' /tmp/render_resp_images.json)"
[ -n "$BN" ] || { echo "[ERR] Render-Antwort ohne Pfad"; exit 1; }

note "Download prüfen (HEAD/GET)"
curl -sS -I "$API/exports/download?name=$BN" | sed -n '1,20p'
curl -sS -G --data-urlencode "name=$BN" -o "/tmp/$BN" "$API/exports/download"
ls -lh "/tmp/$BN"
echo "OK: /tmp/$BN bereit."
