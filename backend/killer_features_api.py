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
