#!/usr/bin/env bash
# =============================================
# Advanced Features + Live Generator Installation
# =============================================
# Installiert:
# - Slide DNA Analyzer
# - Semantic Slide Matcher
# - Brand Voice Extractor
# - Argument Engine (Chain Builder, Objections, Consistency)
# - Content Intelligence (Evidence, Complexity, Recommender)
# - Live Generator (Gamma.app-ähnlich)

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Advanced Features + Live Generator Installation       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Backup
echo "[1/6] Erstelle Backup..."
BACKUP_DIR="backups/advanced_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp backend/agent_v3_api.py "$BACKUP_DIR/" 2>/dev/null || true
echo "  ✓ Backup erstellt"

# 2. Services installieren
echo ""
echo "[2/6] Installiere Advanced Feature Services..."

FILES=(
    "slide_dna_analyzer.py"
    "semantic_slide_matcher.py"
    "brand_voice_extractor.py"
    "argument_engine.py"
    "content_intelligence.py"
    "live_generator.py"
    "live_generator_api.py"
)

MISSING=""
for file in "${FILES[@]}"; do
    if [[ ! -f ~/Downloads/$file ]]; then
        MISSING="$MISSING $file"
    fi
done

if [[ -n "$MISSING" ]]; then
    echo "  ⚠ Fehlende Dateien:$MISSING"
    echo "  Bitte erst alle Dateien herunterladen!"
    exit 1
fi

# Services kopieren
for file in "${FILES[@]}"; do
    if [[ "$file" == *"_api.py" ]]; then
        cp ~/Downloads/$file backend/
        echo "  ✓ backend/$file"
    else
        cp ~/Downloads/$file services/
        echo "  ✓ services/$file"
    fi
done

# 3. Test Imports
echo ""
echo "[3/6] Teste Imports..."
source .venv/bin/activate
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

modules = [
    ("services.slide_dna_analyzer", "analyze_all_templates"),
    ("services.semantic_slide_matcher", "find_similar_slides"),
    ("services.brand_voice_extractor", "build_voice_profile"),
    ("services.argument_engine", "build_argument_chain"),
    ("services.content_intelligence", "recommend_template"),
    ("services.live_generator", "start_generation"),
]

for module, func in modules:
    try:
        mod = __import__(module, fromlist=[func])
        getattr(mod, func)
        print(f"  ✓ {module.split('.')[-1]}")
    except Exception as e:
        print(f"  ✗ {module.split('.')[-1]}: {e}")
EOF

# 4. Patch Agent V3.6 → V3.7
echo ""
echo "[4/6] Patche Agent V3.6 → V3.7..."
python3 << 'PATCH'
filepath = "backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# Version update
content = content.replace('"version": "3.6",', '"version": "3.7",')

# Add advanced features flag
if "HAS_ADVANCED_FEATURES" not in content:
    old = "HAS_KILLER_FEATURES = True"
    new = """HAS_KILLER_FEATURES = True

# Advanced Features (Stufe 7)
try:
    from services.slide_dna_analyzer import extract_slide_dna, get_optimal_structure
    from services.semantic_slide_matcher import get_slide_suggestions
    from services.brand_voice_extractor import get_writing_guidelines
    from services.argument_engine import check_deck_consistency
    from services.content_intelligence import score_deck_complexity, detect_knowledge_gaps
    from services.live_generator import live_generator
    HAS_ADVANCED_FEATURES = True
except ImportError as e:
    HAS_ADVANCED_FEATURES = False
    print(f"Advanced Features nicht verfügbar: {e}")"""
    
    if old in content:
        content = content.replace(old, new)
        print("✓ Advanced Features Import hinzugefügt")

# Add to services dict
if '"advanced_features":' not in content:
    old = '"killer_features": HAS_KILLER_FEATURES,'
    new = '''"killer_features": HAS_KILLER_FEATURES,
            "advanced_features": HAS_ADVANCED_FEATURES,
            "live_generator": HAS_ADVANCED_FEATURES,'''
    if old in content:
        content = content.replace(old, new)
        print("✓ Services erweitert")

print("✓ Version auf 3.7 aktualisiert")

with open(filepath, "w") as f:
    f.write(content)
PATCH

# 5. Initiales DNA-Scanning
echo ""
echo "[5/6] Führe initiales Template-Scanning durch..."
python3 << 'SCAN'
import sys
sys.path.insert(0, '.')

print("  Analysiere Templates (DNA)...")
try:
    from services.slide_dna_analyzer import analyze_all_templates
    result = analyze_all_templates()
    print(f"  ✓ {result.get('analyzed', 0)} Templates analysiert")
except Exception as e:
    print(f"  ⚠ DNA-Analyse: {e}")

print("  Indiziere Templates (Semantic)...")
try:
    from services.semantic_slide_matcher import index_all_templates
    result = index_all_templates()
    print(f"  ✓ {result.get('indexed_slides', 0)} Slides indiziert")
except Exception as e:
    print(f"  ⚠ Semantic Index: {e}")

print("  Baue Voice Profile...")
try:
    from services.brand_voice_extractor import build_voice_profile
    profile = build_voice_profile("default")
    print(f"  ✓ Voice Profile erstellt ({profile.templates_analyzed} Templates)")
except Exception as e:
    print(f"  ⚠ Voice Profile: {e}")
SCAN

# 6. API neu starten
echo ""
echo "[6/6] Starte API neu..."
pkill -f gunicorn || true
sleep 2

nohup .venv/bin/gunicorn backend.api:app \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8011 \
    --timeout 300 \
    > logs/gunicorn.log 2>&1 &

sleep 5

if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "  ✓ API läuft"
else
    echo "  ⚠ API nicht erreichbar"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Advanced Features Installation abgeschlossen!       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Slide DNA Analyzer (Template-Muster)"
echo "  ✓ Semantic Slide Matcher (Ähnliche Slides finden)"
echo "  ✓ Brand Voice Extractor (Dein Schreibstil)"
echo "  ✓ Argument Chain Builder"
echo "  ✓ Objection Handler"
echo "  ✓ Consistency Checker"
echo "  ✓ Evidence Linker"
echo "  ✓ Complexity Scorer"
echo "  ✓ Template Recommender"
echo "  ✓ Knowledge Gap Detector"
echo "  ✓ Live Generator (Gamma.app-Style)"
echo ""
echo "Neue API Endpoints:"
echo "  POST /live/start          - Starte Live-Generierung"
echo "  GET  /live/stream/{id}    - SSE Stream für Updates"
echo "  GET  /live/progress/{id}  - Polling für Fortschritt"
echo "  GET  /live/preview/{id}/{slide} - Slide Preview"
echo "  POST /live/edit/{id}      - Slide bearbeiten"
echo "  POST /live/cancel/{id}    - Abbrechen"
echo "  POST /live/export/{id}    - Exportieren"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/live/status | python3 -m json.tool'
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
