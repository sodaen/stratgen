# -*- coding: utf-8 -*-
"""
backend/orchestrator_api.py
===========================
API Endpoints für Feature Orchestrator

Ermöglicht direkten Zugriff auf orchestrierte Analysen und QA.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

# ============================================
# IMPORTS
# ============================================

try:
    from services.feature_orchestrator import (
        orchestrate_analysis,
        orchestrate_quality_check,
        check_status as orchestrator_status,
        orchestrator
    )
    HAS_ORCHESTRATOR = True
except ImportError as e:
    HAS_ORCHESTRATOR = False
    print(f"Orchestrator Import Error: {e}")


# ============================================
# MODELS
# ============================================

class AnalysisRequest(BaseModel):
    topic: str
    brief: str
    customer_name: str = ""
    industry: str = ""
    audience: str = ""
    deck_size: str = "medium"


class QARequest(BaseModel):
    slides: List[Dict[str, Any]]
    topic: str = ""
    industry: str = ""


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
def api_orchestrator_status():
    """Status des Feature Orchestrators."""
    if not HAS_ORCHESTRATOR:
        return {"ok": False, "error": "Orchestrator nicht verfügbar"}
    return orchestrator_status()


@router.post("/analyze")
def api_orchestrated_analysis(req: AnalysisRequest):
    """
    Führt orchestrierte Analyse durch.
    
    Nutzt automatisch alle verfügbaren Features:
    - Briefing Analyzer
    - Story Engine
    - Persona Engine
    - Slide DNA
    - Semantic Matcher
    - Brand Voice
    - Knowledge Search
    - Competitive Intel (wenn relevant)
    - ROI Calculator (wenn relevant)
    """
    if not HAS_ORCHESTRATOR:
        raise HTTPException(500, "Orchestrator nicht verfügbar")
    
    return orchestrate_analysis(
        topic=req.topic,
        brief=req.brief,
        customer_name=req.customer_name,
        industry=req.industry,
        audience=req.audience,
        deck_size=req.deck_size
    )


@router.post("/qa")
def api_quality_check(req: QARequest):
    """
    Führt orchestrierte Qualitätsprüfung durch.
    
    Prüft:
    - Consistency (Zahlen, Begriffe, Ton)
    - Complexity (Lesbarkeit pro Slide)
    - Evidence (Belegte Behauptungen)
    - Objections (Mögliche Einwände)
    """
    if not HAS_ORCHESTRATOR:
        raise HTTPException(500, "Orchestrator nicht verfügbar")
    
    return orchestrate_quality_check(
        slides=req.slides,
        topic=req.topic,
        industry=req.industry
    )


@router.post("/full-pipeline")
def api_full_pipeline(req: AnalysisRequest):
    """
    Führt vollständige Pipeline durch:
    1. Orchestrierte Analyse
    2. Gibt Empfehlungen für Generierung
    
    Nützlich für Frontend um alle Infos vor Generierung zu haben.
    """
    if not HAS_ORCHESTRATOR:
        raise HTTPException(500, "Orchestrator nicht verfügbar")
    
    # Analyse
    analysis_result = orchestrate_analysis(
        topic=req.topic,
        brief=req.brief,
        customer_name=req.customer_name,
        industry=req.industry,
        audience=req.audience,
        deck_size=req.deck_size
    )
    
    if not analysis_result.get("ok"):
        return analysis_result
    
    analysis = analysis_result.get("analysis", {})
    
    # Empfehlungen zusammenstellen
    recommendations = {
        "structure": analysis.get("recommended_structure", []),
        "framework": analysis.get("recommended_framework", "problem_solution"),
        "template": analysis.get("template_recommendation", ""),
        "voice": analysis.get("writing_guidelines", {}),
        "facts_available": len(analysis.get("relevant_facts", [])),
        "knowledge_gaps": analysis.get("knowledge_gaps", []),
        "briefing_quality": analysis.get("briefing_quality", 0),
        "missing_info": analysis.get("briefing_gaps", [])
    }
    
    # Warnung wenn Briefing-Qualität niedrig
    warnings = []
    if recommendations["briefing_quality"] < 50:
        warnings.append("Briefing-Qualität ist niedrig. Mehr Details würden bessere Ergebnisse liefern.")
    if recommendations["knowledge_gaps"]:
        warnings.append(f"Wissenslücken erkannt: {len(recommendations['knowledge_gaps'])} Themen")
    
    return {
        "ok": True,
        "analysis": analysis,
        "recommendations": recommendations,
        "warnings": warnings,
        "ready_for_generation": recommendations["briefing_quality"] >= 30
    }


@router.get("/features")
def api_list_features():
    """Listet alle verfügbaren Features des Orchestrators."""
    if not HAS_ORCHESTRATOR:
        raise HTTPException(500, "Orchestrator nicht verfügbar")
    
    status = orchestrator_status()
    features = status.get("features", {})
    
    feature_descriptions = {
        "briefing_analyzer": "Analysiert Briefing-Qualität und erkennt fehlende Infos",
        "story_engine": "Erkennt passendes Story-Framework (AIDA, SCQA, etc.)",
        "persona_engine": "Analysiert Zielgruppe und generiert Personas",
        "competitive": "SWOT-Analyse und Wettbewerber-Infos",
        "roi": "Business Case und ROI-Berechnung",
        "dna": "Lernt aus Templates die optimale Struktur",
        "semantic": "Findet ähnliche Slides aus Templates",
        "voice": "Extrahiert und wendet Schreibstil an",
        "arguments": "Baut Argumentationsketten und findet Einwände",
        "content_intel": "Prüft Komplexität und verlinkt Belege",
        "knowledge": "Sucht relevante Fakten aus Knowledge Base"
    }
    
    return {
        "ok": True,
        "features": [
            {
                "id": k,
                "available": v,
                "description": feature_descriptions.get(k, "")
            }
            for k, v in features.items()
        ],
        "available_count": status.get("features_available", 0),
        "total_count": status.get("features_total", 0)
    }
