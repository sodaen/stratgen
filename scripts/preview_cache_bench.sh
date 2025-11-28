#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8011}"
TTL="${TTL:-60}"
TOPIC_RAW="${1:-Short paragraph that mentions: purple-elephant RAG smoketest $(date +%s)}"
TOPIC=$(jq -rn --arg s "$TOPIC_RAW" '$s|@uri')

meas () { curl -s -w "time_total=%{time_total}\n" -o /dev/null "$BASE/content/preview?topic=$TOPIC&k=3"; }

echo "First call (MISS expected):"; meas
echo "Second call (HIT expected):"; meas
echo "After TTL (MISS again):"; sleep "$TTL"; meas
