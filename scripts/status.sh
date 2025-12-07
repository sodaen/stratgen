#!/bin/bash
#
# STRATGEN STATUS CHECK
#

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN - SYSTEM STATUS                                ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Services
echo "SERVICES:"
for svc in nginx stratgen stratgen-frontend redis-server ollama; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  ✓ $svc: running"
    else
        echo "  ✗ $svc: stopped"
    fi
done

echo ""
echo "PORTS:"
for port in 80 3000 8011 6333 6379 11434; do
    if curl -s "http://localhost:$port" > /dev/null 2>&1 || \
       curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✓ Port $port: open"
    else
        echo "  ✗ Port $port: closed"
    fi
done

echo ""
echo "UNIFIED STATUS:"
curl -s "http://localhost:8011/unified/status" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for name, info in d.get('services', {}).items():
        status = info.get('status', 'unknown')
        symbol = '✓' if status == 'online' else '✗'
        print(f'  {symbol} {name}: {status}')
except:
    print('  ✗ Nicht erreichbar')
" || echo "  ✗ Backend nicht erreichbar"

echo ""
echo "OLLAMA MODELLE:"
curl -s "http://localhost:11434/api/tags" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for m in d.get('models', []):
        print(f'  - {m[\"name\"]}')
except:
    print('  ✗ Ollama nicht erreichbar')
" || echo "  ✗ Ollama nicht erreichbar"
