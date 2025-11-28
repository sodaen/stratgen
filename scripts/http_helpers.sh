#!/usr/bin/env bash
set -u  # kein -e/-o pipefail -> robuste Ausgabe statt Abbruch

API="${API:-http://127.0.0.1:8011}"
KEY="${STRATGEN_API_KEY:-}"

declare -a HDR=()
[ -n "${KEY:-}" ] && HDR=(-H "X-API-Key: $KEY")

post_json () {
  # usage: post_json "URL" '{"json":"body"}'
  local url="$1"
  local body="${2:-{}}"
  curl -sS "${HDR[@]}" -H "Content-Type: application/json" -X POST --data "$body" "$url"
}

get_json () {
  # usage: get_json "URL"
  local url="$1"
  curl -sS "${HDR[@]}" -H "Accept: application/json" "$url"
}

head_download () {
  # usage: head_download "filename.ext"
  local name="$1"
  curl -sI "${HDR[@]}" --get --data-urlencode "name=$name" "$API/exports/download"
}

get_download () {
  # usage: get_download "filename.ext"
  local name="$1"
  local out="/tmp/$name"
  curl -s  "${HDR[@]}" --get --data-urlencode "name=$name" -o "$out" "$API/exports/download"
  ls -lh "$out"
}
