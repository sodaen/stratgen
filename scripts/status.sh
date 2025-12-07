#!/bin/bash
#
# STRATGEN STATUS CHECK
#

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN - SYSTEM STATUS                                ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Services (inkl. Snap)
echo "SERVICES:"
for svc in nginx stratgen stratgen-frontend ollama; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  ✓ $svc: running"
    else
        echo "  ✗ $svc: stopped"
    fi
done

# Redis (Snap oder systemd)
if pgrep -x "redis-server" > /dev/null 2>&1; then
    echo "  ✓ redis: running ($(pgrep -x redis-server | wc -l) process)"
elif systemctl is-active --quiet redis-server 2>/dev/null; then
    echo "  ✓ redis-server: running"
else
    echo "  ✗ redis: stopped"
fi

# Qdrant
if pgrep -x "qdrant" > /dev/null 2>&1 || systemctl is-active --quiet qdrant 2>/dev/null; then
    echo "  ✓ qdrant: running"
else
    echo "  ✗ qdrant: stopped"
fi

# Celery
if pgrep -f "celery.*worker" > /dev/null 2>&1; then
    echo "  ✓ celery: running ($(pgrep -f 'celery.*worker' | wc -l) workers)"
else
    echo "  ✗ celery: stopped"
fi

echo ""
echo "PORTS:"
for port in 80 3000 8011 6333 6379 11434; do
    if nc -z localhost $port 2>/dev/null || redis-cli -p $port ping 2>/dev/null | grep -q PONG; then
        echo "  ✓ Port $port: open"
    elif curl -s --max-time 1 "http://localhost:$port" > /dev/null 2>&1; then
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
    print()
    print(f'  Knowledge: {d.get(\"knowledge\", {}).get(\"total_chunks\", 0)} Chunks')
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
        size_gb = m.get('size', 0) / (1024**3)
        print(f'  - {m[\"name\"]} ({size_gb:.1f} GB)')
except:
    print('  ✗ Ollama nicht erreichbar')
" || echo "  ✗ Ollama nicht erreichbar"
