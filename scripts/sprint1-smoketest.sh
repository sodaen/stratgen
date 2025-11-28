#!/usr/bin/env bash
set -euo pipefail
base="127.0.0.1:8011"
echo "Routes:"; curl -sS $base/ | jq '.routes | map(select(test("^/(content|knowledge)/")))'
echo "Health:"; curl -sS $base/health | jq .
echo "Scan:";   curl -sS -X POST $base/knowledge/scan | jq .
echo "Embed:";  curl -sS -X POST "$base/knowledge/embed_local?model=sbert:sentence-transformers/all-MiniLM-L6-v2" | jq .
echo "SemSearch:"; curl -sS "$base/knowledge/search_semantic?q=ueberblick&k=5" | jq .
echo "Preview:"; curl -sS "$base/content/preview?topic=ACME%20Pitch%20%C3%9Cberblick" | jq .
echo "Preview+Sources:"; curl -sS "$base/content/preview_with_sources?topic=ACME%20Pitch%20%C3%9Cberblick&k=5" | jq .
cat > /tmp/generate_payload.json <<'JSON'
{ "topic":"ACME Pitch – Überblick", "k":5, "style":"b2b_de_sachlich", "sections":["Ziele","Programm","Roadmap"] }
JSON
echo "Generate:"; curl -sS -X POST $base/content/generate -H 'Content-Type: application/json' -d @/tmp/generate_payload.json | jq .
