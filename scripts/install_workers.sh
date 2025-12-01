#!/usr/bin/env bash
# =============================================
# Distributed Worker System Installation
# =============================================
# Installiert:
# - Redis (Message Queue)
# - Celery (Task Queue)
# - Worker Tasks (LLM, Analysis, Generation, Export)
# - Worker API

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Distributed Worker System Installation                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Redis installieren
echo "[1/6] Prüfe Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "  Redis nicht gefunden. Installiere..."
    sudo apt-get update
    sudo apt-get install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
fi

# Redis Status
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✓ Redis läuft"
else
    echo "  Starte Redis..."
    sudo systemctl start redis-server
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "  ✓ Redis gestartet"
    else
        echo "  ✗ Redis konnte nicht gestartet werden!"
        exit 1
    fi
fi

# 2. Python Dependencies
echo ""
echo "[2/6] Installiere Python Dependencies..."
source .venv/bin/activate
pip install celery[redis] redis --quiet
echo "  ✓ celery, redis installiert"

# 3. Worker-Verzeichnis erstellen
echo ""
echo "[3/6] Erstelle Worker-Struktur..."
mkdir -p workers/tasks
touch workers/__init__.py
touch workers/tasks/__init__.py

# 4. Worker-Dateien installieren
echo ""
echo "[4/6] Installiere Worker-Dateien..."

cp ~/Downloads/celery_app.py workers/
cp ~/Downloads/llm_tasks.py workers/tasks/
cp ~/Downloads/analysis_tasks.py workers/tasks/
cp ~/Downloads/generation_tasks.py workers/tasks/
cp ~/Downloads/export_tasks.py workers/tasks/
cp ~/Downloads/workers_api.py backend/

echo "  ✓ celery_app.py"
echo "  ✓ llm_tasks.py"
echo "  ✓ analysis_tasks.py"
echo "  ✓ generation_tasks.py"
echo "  ✓ export_tasks.py"
echo "  ✓ workers_api.py"

# 5. Test Imports
echo ""
echo "[5/6] Teste Imports..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from workers.celery_app import app
    print("  ✓ celery_app")
except Exception as e:
    print(f"  ✗ celery_app: {e}")

try:
    from workers.tasks.llm_tasks import generate_content
    print("  ✓ llm_tasks")
except Exception as e:
    print(f"  ✗ llm_tasks: {e}")

try:
    from workers.tasks.analysis_tasks import analyze_briefing
    print("  ✓ analysis_tasks")
except Exception as e:
    print(f"  ✗ analysis_tasks: {e}")

try:
    from workers.tasks.generation_tasks import generate_slide
    print("  ✓ generation_tasks")
except Exception as e:
    print(f"  ✗ generation_tasks: {e}")

try:
    from workers.tasks.export_tasks import export_pptx
    print("  ✓ export_tasks")
except Exception as e:
    print(f"  ✗ export_tasks: {e}")
EOF

# 6. API neu starten
echo ""
echo "[6/6] Starte API neu..."
pkill -f gunicorn || true
sleep 2

nohup .venv/bin/gunicorn backend.api:app \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8011 \
    --timeout 300 \
    > logs/gunicorn.log 2>&1 &

sleep 3

if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "  ✓ API läuft"
else
    echo "  ⚠ API nicht erreichbar"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Distributed Worker System installiert!              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Worker starten (in separatem Terminal):"
echo "   cd ~/stratgen && source .venv/bin/activate"
echo "   celery -A workers.celery_app worker --loglevel=info -Q default,llm,analysis,generation,export"
echo ""
echo "2. Status prüfen:"
echo "   curl http://localhost:8011/workers/status | python3 -m json.tool"
echo ""
echo "3. Task einreichen:"
echo '   curl -X POST http://localhost:8011/workers/tasks/submit \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '\''{"task_type": "analysis", "task_name": "briefing", "params": {"brief": "Test", "topic": "Test"}}'\'''
echo ""
echo "Queues:"
echo "  • default  - Allgemeine Tasks"
echo "  • llm      - GPU-intensive LLM Tasks"
echo "  • analysis - CPU-intensive Analyse"
echo "  • generation - Slide-Generierung"
echo "  • export   - PPTX/PDF Export"
