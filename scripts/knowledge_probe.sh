#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

OPJ="$TMP/openapi.json"
curl -fsS "$BASE/openapi.json" -o "$OPJ"

METHOD=$(jq -r '.paths["/knowledge/search_semantic"] | keys[]' "$OPJ" | head -n1)
if [ -z "${METHOD:-}" ] || [ "$METHOD" = "null" ]; then
  echo "❌ Endpoint /knowledge/search_semantic nicht in OpenAPI"; exit 2
fi
echo "METHOD=$METHOD"

FIELD=""
if [ "$METHOD" = "post" ]; then
  FIELD=$(jq -r '
    .paths["/knowledge/search_semantic"].post.requestBody
    .content["application/json"].schema.properties
    | keys[] | select(test("(?i)q|query|text|input"))
  ' "$OPJ" | head -n1)
else
  FIELD=$(jq -r '
    .paths["/knowledge/search_semantic"].get.parameters[]
    .name | select(test("(?i)q|query|text|input"))
  ' "$OPJ" | head -n1)
fi
FIELD="${FIELD:-q}"
echo "FIELD=$FIELD"

QUERY="postproduktion transkription broadcast"

OUT="$TMP/knowledge.json"
HTTP=0
if [ "$METHOD" = "post" ]; then
  BODY=$(jq -nc --arg k "$FIELD" --arg v "$QUERY" '{($k):$v}')
  HTTP=$(curl --fail-with-body -sS -w '%{http_code}\n' -o "$OUT" \
    -H 'content-type: application/json' -X POST "$BASE/knowledge/search_semantic" -d "$BODY" | tail -n1 || true)
else
  Q=$(python3 - <<PY
import urllib.parse, os
print(urllib.parse.urlencode({os.environ.get("FIELD","q"): os.environ.get("QUERY","")}))
PY
)
  HTTP=$(curl --fail-with-body -sS -w '%{http_code}\n' -o "$OUT" \
    "$BASE/knowledge/search_semantic?$Q" | tail -n1 || true)
fi
echo "HTTP=$HTTP"
test "$HTTP" = "200" || { echo "❌ Request fehlgeschlagen"; cat "$OUT" 2>/dev/null || true; exit 3; }

echo "== Treffer-Zusammenfassung =="
jq '{
  hits: ( .hits // .results // [] | length ),
  sample: ( .hits // .results // [] | [.[0:3][] | {title:(.title//.name//.id), score:(.score//.relevance//null)}] )
}' "$OUT"

HITS=$(jq -r '( .hits // .results // [] | length )' "$OUT")
if [ "${HITS:-0}" -lt 1 ]; then
  echo "⚠️  Keine Treffer zurückgegeben (Quelle leer oder Index/Wiring prüfen)."
else
  echo "✅ Treffer: $HITS"
fi

exit 0
