#!/usr/bin/env bash
set -Eeuo pipefail
API="${API:-http://127.0.0.1:8011}"

fail(){ echo "✖ $*" >&2; exit 1; }
ok(){ echo "✔ $*"; }

jq -r '."status"' <(curl -sS "$API/health") | grep -q '^ok$' || fail "health"
ok "health"

REQ='{"customer_name":"Acme GmbH","topic":"Go-to-Market 2026 (RAG)","query":"ISO27001 SOC2 ROI 90 Tage"}'
COMPOSE="$(curl -sS -X POST "$API/content/compose" -H "Content-Type: application/json" --data "$REQ")"
TITLE="$(jq -r '.title // empty' <<<"$COMPOSE")"
PLEN="$(jq -r '.plan|length // 0' <<<"$COMPOSE")"
[ "$PLEN" -gt 0 ] || fail "compose produced empty plan"
ok "compose ($PLEN slides)"

TITLE_FIXED="$(sed -E 's/\(RAG\) \(RAG\)/(RAG)/g' <<<"$TITLE")"
OUT="data/exports/Acme_GmbH_Smoke.pptx"
RENDER_REQ="$(jq -n --arg t "$TITLE_FIXED" --arg o "$OUT" --argjson plan "$(jq '.plan' <<<"$COMPOSE")" '{title:$t, plan:$plan, out_path:$o}')"
jq -e . >/dev/null <<<"$RENDER_REQ" || fail "render req json"

curl -sS -X POST "$API/pptx/render" -H "Content-Type: application/json" --data "$RENDER_REQ" \
| jq -e '.ok == true' >/dev/null || fail "render"
[ -s "$OUT" ] || fail "render output missing"
ok "render -> $OUT ($(wc -c <"$OUT") bytes)"

LATEST="$(curl -sS "$API/exports/latest" | jq -r '.latest.name // empty')"
[ -n "$LATEST" ] || fail "exports/latest empty"
HEAD_CODE="$(curl -sS -o /dev/null -w '%{http_code}' -I "$API/exports/download?name=$LATEST")"
[ "$HEAD_CODE" = "200" ] || fail "download HEAD != 200"
TMP="/tmp/$LATEST"
curl -sS -L "$API/exports/download?name=$LATEST" -o "$TMP"
[ -s "$TMP" ] || fail "download GET empty"
ok "download ok ($TMP)"
echo "✔ SMOKE: all good."
