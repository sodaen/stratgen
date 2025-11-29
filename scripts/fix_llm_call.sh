#!/usr/bin/env bash
# =============================================
# Fix: Agent V3.1 LLM-Aufruf korrigieren
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  Fix: Agent V3.1 LLM-Aufruf                ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Patch herunterladen und ausführen
if [[ -f ~/Downloads/patch_llm_call.py ]]; then
    source .venv/bin/activate
    python3 ~/Downloads/patch_llm_call.py
else
    echo "✗ patch_llm_call.py nicht in Downloads!"
    exit 1
fi

# 2. API neu starten
echo ""
echo "Starte API neu..."
pkill -f gunicorn || true
sleep 2
~/stratgen/scripts/startup_prod.sh

# 3. Test
echo ""
echo "=== Teste Agent V3.1 ==="
sleep 3

curl -X POST http://localhost:8011/agent/run_v3 \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Digitale Transformation",
    "brief": "Strategie für KMU",
    "deck_size": "short",
    "auto_improve": false
  }' 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✓ OK: {data.get(\"ok\")}')
print(f'✓ Slides: {data.get(\"slide_count\")}')
print(f'✓ Quality: {data.get(\"quality_score\")}')
print(f'✓ Duration: {data.get(\"duration_s\")}s')
if data.get('slides'):
    s = data['slides'][1] if len(data['slides']) > 1 else data['slides'][0]
    bullets = s.get('bullets', [])
    print(f'✓ Sample bullets: {bullets[:2]}')
    if 'Generierung:' in str(bullets):
        print('⚠ LLM-Fehler in bullets!')
    else:
        print('✓ LLM-Generierung funktioniert!')
"
