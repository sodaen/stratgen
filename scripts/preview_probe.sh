#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# Defaults können per ENV überschrieben werden:
TEXT="${TEXT:-Erkläre in 4–6 Bulletpoints den Nutzen von KI-Transkription in der Broadcast-Postproduktion und nenne Quellen.}"
TOPIC="${TOPIC:-KI in der Postproduktion (Broadcast)}"

echo "== Discover method & schema from OpenAPI =="
OPJ="$TMP/openapi.json"
curl -fsS "$BASE/openapi.json" -o "$OPJ"

METHOD=$(jq -r '.paths["/content/preview_with_sources"] | keys[]' "$OPJ" | head -n1)
[ -n "${METHOD:-}" ] && [ "$METHOD" != "null" ] || { echo "❌ Endpoint fehlt"; exit 2; }
echo "METHOD=$METHOD"

build_payload_get() {
  jq -n \
    --arg text "$TEXT" \
    --arg topic "$TOPIC" \
    --argjson params "$(jq '.paths["/content/preview_with_sources"].get.parameters' "$OPJ")" '
      reduce ($params // [])[] as $p ({};
        . + {
          ($p.name):
            ( if ($p.name|test("(?i)text|prompt|input|q|query")) then $text
              elif ($p.name|test("(?i)topic|subject|title")) then $topic
              else ($p.schema.default // $p.example // $p.schema.example // "")
              end )
        }
      )'
}

build_payload_post() {
  # required-Felder aus dem Schema erkennen und füllen
  jq -n \
    --arg text "$TEXT" \
    --arg topic "$TOPIC" \
    --argjson props "$(jq '.paths["/content/preview_with_sources"].post.requestBody.content["application/json"].schema.properties' "$OPJ")" \
    --argjson req  "$(jq '.paths["/content/preview_with_sources"].post.requestBody.content["application/json"].schema.required // []' "$OPJ")" '
      def pick_default($p):
        ($p.default // $p.example // $p.schema.example // "");
      reduce ($props|to_entries[])[] as $e ({};
        . + {
          ($e.key):
            ( if ($e.key|test("(?i)text|prompt|input|q|query")) then $text
              elif ($e.key|test("(?i)topic|subject|title")) then $topic
              else pick_default($e.value)
              end )
        }
      )
      | with_entries(
          # nur required Felder + erkannte (text/topic) schicken; andere optional weglassen
          ( .key as $k
            | if ( ($k|test("(?i)text|prompt|input|q|query")) or ($k|test("(?i)topic|subject|title")) or ($req|index($k)) )
              then .
              else empty
              end )
        )'
}

echo "== Build request =="
OUT="$TMP/preview.json"
HTTP=0

if [ "$METHOD" = "get" ]; then
  PAY=$(build_payload_get)
  echo "QueryMap: $PAY"
  Q=$(echo "$PAY" | python3 -c 'import json,sys,urllib.parse;print(urllib.parse.urlencode(json.load(sys.stdin)))')
  HTTP=$(curl --fail-with-body -sS -w '%{http_code}\n' -o "$OUT" "$BASE/content/preview_with_sources?$Q" | tail -n1 || true)
else
  BODY=$(build_payload_post)
  echo "Body: $BODY"
  HTTP=$(curl --fail-with-body -sS -w '%{http_code}\n' -o "$OUT" \
    -H 'content-type: application/json' -X POST "$BASE/content/preview_with_sources" -d "$BODY" | tail -n1 || true)
fi

echo "HTTP=$HTTP"
[ "$HTTP" = "200" ] || { echo "❌ Request fehlgeschlagen"; cat "$OUT" 2>/dev/null || true; exit 3; }

echo "== Ergebnis (gekürzt) =="
jq '{
  has_text: (has("text") or has("content") or has("preview")),
  sources_len: (if has("sources") then (.sources|length)
                elif has("citations") then (.citations|length)
                else 0 end)
}' "$OUT"

SRC_LEN=$(jq -r 'if has("sources") then (.sources|length)
                 elif has("citations") then (.citations|length)
                 else 0 end' "$OUT")
if [ "${SRC_LEN:-0}" -lt 1 ]; then
  echo "⚠️  Keine Quellen im Response gefunden."
else
  echo "✅ Quellen vorhanden: $SRC_LEN"
fi
