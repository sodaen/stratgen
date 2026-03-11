#!/bin/bash
# StratGen Deploy + Wait Helper
# Verwendung: bash deploy_wait.sh [max_seconds]
# Nach jedem: sudo systemctl restart stratgen && bash deploy_wait.sh

MAX=${1:-60}
URL="http://localhost:8011/offline/status"
INTERVAL=2
elapsed=0

echo "⏳ Warte auf Backend (max ${MAX}s)..."

while [ $elapsed -lt $MAX ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo "✅ Backend bereit nach ${elapsed}s"
        echo ""
        # Kurz-Status anzeigen
        curl -s "$URL" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f\"  Offline-Mode: {d['offline_mode']}\")
print(f\"  Uptime: {d['uptime_seconds']}s\")
"
        exit 0
    fi
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    echo -n "."
done

echo ""
echo "❌ Backend nach ${MAX}s nicht erreichbar"
echo "→ sudo journalctl -u stratgen -n 20 --no-pager | tail -10"
exit 1
