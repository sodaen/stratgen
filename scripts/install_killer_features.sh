#!/usr/bin/env bash
# =============================================
# Killer-Features Installation
# =============================================
# Installiert alle erweiterten Features:
# - Persona & Archetypen Engine
# - Competitive Intelligence
# - ROI Calculator & Business Case
# - Story & Narrative Engine
# - Smart Briefing Analyzer
# - Auto-Learner Fix

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Killer-Features Installation                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Backup erstellen
echo "[1/7] Erstelle Backup..."
BACKUP_DIR="backups/killer_features_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp backend/agent_v3_api.py "$BACKUP_DIR/" 2>/dev/null || true
echo "  ✓ Backup erstellt in $BACKUP_DIR"

# 2. Services installieren
echo ""
echo "[2/7] Installiere Killer-Feature Services..."

# Prüfen ob Dateien existieren
MISSING_FILES=""
for file in persona_engine.py competitive_intelligence.py roi_calculator.py story_engine.py briefing_analyzer.py auto_learner.py; do
    if [[ ! -f ~/Downloads/$file ]]; then
        MISSING_FILES="$MISSING_FILES $file"
    fi
done

if [[ -n "$MISSING_FILES" ]]; then
    echo "  ⚠ Fehlende Dateien in ~/Downloads:$MISSING_FILES"
    echo "  Bitte erst alle Dateien herunterladen!"
    exit 1
fi

cp ~/Downloads/persona_engine.py services/
cp ~/Downloads/competitive_intelligence.py services/
cp ~/Downloads/roi_calculator.py services/
cp ~/Downloads/story_engine.py services/
cp ~/Downloads/briefing_analyzer.py services/
cp ~/Downloads/auto_learner.py services/

echo "  ✓ persona_engine.py"
echo "  ✓ competitive_intelligence.py"
echo "  ✓ roi_calculator.py"
echo "  ✓ story_engine.py"
echo "  ✓ briefing_analyzer.py"
echo "  ✓ auto_learner.py (mit Fix)"

# 3. Test Imports
echo ""
echo "[3/7] Teste Imports..."
source .venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')

services_ok = []
services_fail = []

try:
    from services.persona_engine import generate_persona, list_archetypes
    services_ok.append('persona_engine')
except Exception as e:
    services_fail.append(f'persona_engine: {e}')

try:
    from services.competitive_intelligence import analyze_competition, generate_swot
    services_ok.append('competitive_intelligence')
except Exception as e:
    services_fail.append(f'competitive_intelligence: {e}')

try:
    from services.roi_calculator import generate_business_case, calculate_project_roi
    services_ok.append('roi_calculator')
except Exception as e:
    services_fail.append(f'roi_calculator: {e}')

try:
    from services.story_engine import create_story_structure, list_frameworks
    services_ok.append('story_engine')
except Exception as e:
    services_fail.append(f'story_engine: {e}')

try:
    from services.briefing_analyzer import analyze, BriefingQuality
    services_ok.append('briefing_analyzer')
except Exception as e:
    services_fail.append(f'briefing_analyzer: {e}')

try:
    from services.auto_learner import learn_new_files, get_status
    services_ok.append('auto_learner')
except Exception as e:
    services_fail.append(f'auto_learner: {e}')

for s in services_ok:
    print(f'  ✓ {s}')
for s in services_fail:
    print(f'  ✗ {s}')
"

# 4. Agent V3 Patch vorbereiten
echo ""
echo "[4/7] Patche Agent V3.5 → V3.6 (Killer-Features)..."

python3 << 'PATCH_EOF'
import re

filepath = "backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# Patch 1: Killer-Feature Imports hinzufügen
old_multimodal_import = '''# Multi-Modal Export (Stufe 5)
try:
    from services.multimodal_export import'''

new_multimodal_import = '''# Killer-Features (Stufe 6)
try:
    from services.persona_engine import generate_persona, generate_personas, analyze_audience, list_archetypes
    from services.competitive_intelligence import analyze_competition, generate_swot, generate_battle_card
    from services.roi_calculator import generate_business_case, calculate_project_roi
    from services.story_engine import create_story_structure, build_narrative_arc, generate_hooks
    from services.briefing_analyzer import analyze as analyze_briefing, BriefingQuality
    HAS_KILLER_FEATURES = True
except ImportError as e:
    HAS_KILLER_FEATURES = False
    print(f"Killer-Features nicht verfügbar: {e}")

# Multi-Modal Export (Stufe 5)
try:
    from services.multimodal_export import'''

if old_multimodal_import in content:
    content = content.replace(old_multimodal_import, new_multimodal_import)
    print("✓ Patch 1: Killer-Feature Imports hinzugefügt")
else:
    print("⚠ Patch 1: Multi-Modal Import nicht gefunden")

# Patch 2: Version aktualisieren
old_version = '"version": "3.5",'
new_version = '"version": "3.6",'

if old_version in content:
    content = content.replace(old_version, new_version)
    print("✓ Patch 2: Version auf 3.6 aktualisiert")

# Patch 3: Services erweitern
old_services = '"multimodal_export": HAS_MULTIMODAL_EXPORT,'
new_services = '''"multimodal_export": HAS_MULTIMODAL_EXPORT,
            "killer_features": HAS_KILLER_FEATURES,'''

if old_services in content and "killer_features" not in content:
    content = content.replace(old_services, new_services)
    print("✓ Patch 3: killer_features zu services hinzugefügt")

# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Agent V3.5 → V3.6 gepatcht!")
PATCH_EOF

# 5. API Endpoints erstellen
echo ""
echo "[5/7] Erstelle API Endpoints..."

cat > backend/killer_features_api.py << 'API_EOF'
# -*- coding: utf-8 -*-
"""
backend/killer_features_api.py
==============================
API Endpoints für Killer-Features
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/killer", tags=["Killer-Features"])

# ============================================
# IMPORTS
# ============================================

try:
    from services.persona_engine import generate_persona, generate_personas, analyze_audience, list_archetypes
    from services.competitive_intelligence import analyze_competition, generate_swot
    from services.roi_calculator import generate_business_case, calculate_project_roi
    from services.story_engine import create_story_structure, list_frameworks
    from services.briefing_analyzer import analyze as analyze_briefing
    HAS_FEATURES = True
except ImportError as e:
    HAS_FEATURES = False
    print(f"Killer-Features Import Error: {e}")


# ============================================
# MODELS
# ============================================

class BriefingRequest(BaseModel):
    brief: str
    topic: str = ""
    industry: str = ""
    customer_name: str = ""
    audience: str = ""
    goal: str = ""
    deck_size: str = "medium"


class PersonaRequest(BaseModel):
    brief: str
    industry: str = ""
    audience: str = ""
    count: int = 2


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
def killer_status():
    """Status der Killer-Features."""
    return {
        "ok": True,
        "available": HAS_FEATURES,
        "features": [
            "persona_engine",
            "competitive_intelligence", 
            "roi_calculator",
            "story_engine",
            "briefing_analyzer"
        ] if HAS_FEATURES else []
    }


@router.post("/analyze-briefing")
def api_analyze_briefing(req: BriefingRequest):
    """Analysiert ein Briefing vollständig."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    return analyze_briefing(
        brief=req.brief,
        topic=req.topic,
        industry=req.industry,
        customer_name=req.customer_name
    )


@router.post("/personas")
def api_generate_personas(req: PersonaRequest):
    """Generiert Personas aus Briefing."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    personas = generate_personas(
        brief=req.brief,
        industry=req.industry,
        audience=req.audience,
        count=req.count
    )
    
    return {
        "ok": True,
        "personas": [
            {
                "name": p.name,
                "job_title": p.job_title,
                "archetype": p.primary_archetype.value,
                "quote": p.quote,
                "goals": p.goals[:3],
                "challenges": p.challenges[:3]
            }
            for p in personas
        ]
    }


@router.get("/archetypes")
def api_list_archetypes():
    """Listet alle Archetypen."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    return list_archetypes()


@router.post("/competitive")
def api_competitive_analysis(req: BriefingRequest):
    """Führt Wettbewerbsanalyse durch."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    return analyze_competition(
        brief=req.brief,
        topic=req.topic,
        industry=req.industry
    )


@router.post("/swot")
def api_generate_swot(req: BriefingRequest):
    """Generiert SWOT-Analyse."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    swot = generate_swot(
        brief=req.brief,
        topic=req.topic,
        industry=req.industry
    )
    
    return {
        "ok": True,
        "swot": {
            "strengths": swot.strengths,
            "weaknesses": swot.weaknesses,
            "opportunities": swot.opportunities,
            "threats": swot.threats
        }
    }


@router.post("/roi")
def api_calculate_roi(req: BriefingRequest):
    """Berechnet ROI und Business Case."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    return calculate_project_roi(
        brief=req.brief,
        topic=req.topic,
        industry=req.industry
    )


@router.post("/story")
def api_create_story(req: BriefingRequest):
    """Erstellt Story-Struktur."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    
    return create_story_structure(
        brief=req.brief,
        topic=req.topic,
        audience=req.audience,
        goal=req.goal,
        deck_size=req.deck_size
    )


@router.get("/frameworks")
def api_list_frameworks():
    """Listet Story-Frameworks."""
    if not HAS_FEATURES:
        raise HTTPException(500, "Killer-Features nicht verfügbar")
    return list_frameworks()
API_EOF

echo "  ✓ killer_features_api.py erstellt"

# 6. Templates lernen (falls noch nicht gelernt)
echo ""
echo "[6/7] Lerne aus vorhandenen Templates..."
python3 services/auto_learner.py scan 2>&1 | head -10

# 7. API neu starten
echo ""
echo "[7/7] Starte API neu..."
pkill -f gunicorn || true
sleep 2

nohup .venv/bin/gunicorn backend.api:app \
    -w 2 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8011 \
    --timeout 300 \
    > logs/gunicorn.log 2>&1 &

sleep 5

# Test
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "  ✓ API läuft"
else
    echo "  ⚠ API nicht erreichbar - prüfe logs/gunicorn.log"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Killer-Features Installation abgeschlossen!         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Neue Features:"
echo "  ✓ Persona & Archetypen Engine (12 Jung'sche Archetypen)"
echo "  ✓ Competitive Intelligence (SWOT, Battle Cards)"
echo "  ✓ ROI Calculator & Business Case Generator"
echo "  ✓ Story & Narrative Engine (7 Frameworks)"
echo "  ✓ Smart Briefing Analyzer"
echo ""
echo "Neue API Endpoints:"
echo "  POST /killer/analyze-briefing"
echo "  POST /killer/personas"
echo "  POST /killer/competitive"
echo "  POST /killer/swot"
echo "  POST /killer/roi"
echo "  POST /killer/story"
echo "  GET  /killer/archetypes"
echo "  GET  /killer/frameworks"
echo ""
echo "Test mit:"
echo '  curl http://localhost:8011/killer/status | python3 -m json.tool'
echo '  curl http://localhost:8011/agent/v3/status | python3 -m json.tool'
