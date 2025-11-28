# -*- coding: utf-8 -*-
"""
backend/agent_v3.py
===================
Agent V3 - Vollständige Orchestrierung aller Services.

Dieser Agent ersetzt V1 und V2 und verbindet:
- LLM Content Generation (nicht mehr hardcoded!)
- Knowledge/RAG Search
- Asset Tagging & Matching
- Chart Generation
- Template Learning
- Feedback Integration
- PPTX Rendering

Pipeline:
1. BRIEFING    → Parse & Analyse
2. KNOWLEDGE   → RAG Search + Enrichment
3. STRUCTURE   → Outline basierend auf Deck-Size
4. CONTENT     → LLM-generierte Slides
5. VISUALS     → Charts + Asset-Matching
6. CRITIQUE    → Qualitätsprüfung
7. RENDER      → PPTX/PDF/HTML Export
8. FEEDBACK    → Quality Score speichern
"""
from __future__ import annotations
import os
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, BackgroundTasks

# ============================================
# IMPORTS - Services
# ============================================

# LLM Content Generation
try:
    from services.llm_content import (
        generate_bullets,
        generate_summary,
        generate_persona,
        generate_critique,
        generate_metrics,
        generate_slide_content,
        check_ollama
    )
    HAS_LLM_CONTENT = True
except ImportError:
    HAS_LLM_CONTENT = False

# Asset Tagger
try:
    from services.asset_tagger import (
        scan_uploads_directory,
        match_assets_to_slides,
        get_asset_suggestions
    )
    HAS_ASSET_TAGGER = True
except ImportError:
    HAS_ASSET_TAGGER = False

# Chart Generator
try:
    from services.chart_generator import (
        create_bar_chart,
        create_pie_chart,
        create_timeline,
        create_funnel_chart,
        auto_create_chart
    )
    HAS_CHART_GEN = True
except ImportError:
    HAS_CHART_GEN = False

# Template Learner
try:
    from services.template_learner import (
        suggest_structure,
        get_statistics as get_template_stats
    )
    HAS_TEMPLATE_LEARNER = True
except ImportError:
    HAS_TEMPLATE_LEARNER = False

# Feedback Loop
try:
    from services.feedback_loop import (
        get_quality_score,
        get_improvement_suggestions,
        record_feedback
    )
    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False

# Knowledge/RAG
try:
    from services.knowledge import search as knowledge_search, scan_dir as scan_knowledge
except ImportError:
    knowledge_search = None
    scan_knowledge = None

# Generator (für Fallback)
try:
    from services.generator import generate as legacy_generate
except ImportError:
    legacy_generate = None

# ============================================
# KONFIGURATION
# ============================================

API_BASE = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
EXPORTS_DIR = os.getenv("STRATGEN_EXPORTS_DIR", "data/exports")
UPLOADS_DIR = os.getenv("STRATGEN_UPLOADS_DIR", "data/uploads")

# Deck-Size Konfiguration
DECK_SIZES = {
    "short": {"min_slides": 5, "max_slides": 10, "target": 7},
    "medium": {"min_slides": 12, "max_slides": 25, "target": 18},
    "large": {"min_slides": 25, "max_slides": 50, "target": 35},
}

# Slide-Typen für verschiedene Module
SLIDE_MODULES = {
    "title": {"required": True, "order": 0},
    "agenda": {"required": False, "order": 1, "min_size": "medium"},
    "executive_summary": {"required": True, "order": 2},
    "problem": {"required": True, "order": 3},
    "solution": {"required": True, "order": 4},
    "use_cases": {"required": False, "order": 5, "expandable": True},
    "benefits": {"required": True, "order": 6},
    "roi": {"required": False, "order": 7, "min_size": "medium"},
    "roadmap": {"required": True, "order": 8},
    "team": {"required": False, "order": 9, "min_size": "large"},
    "competitive": {"required": False, "order": 10, "min_size": "large"},
    "risks": {"required": False, "order": 11, "min_size": "medium"},
    "next_steps": {"required": True, "order": 12},
    "appendix": {"required": False, "order": 13, "min_size": "large"},
    "contact": {"required": True, "order": 14},
}

# ============================================
# ROUTER & MODELS
# ============================================

router = APIRouter(prefix="/agent", tags=["agent-v3"])


class AgentV3Request(BaseModel):
    """Request für Agent V3 Run."""
    # Briefing
    topic: str
    brief: str = ""
    customer_name: str = ""
    industry: str = ""
    audience: str = ""
    
    # Konfiguration
    deck_size: str = "medium"  # short, medium, large
    language: str = "de"
    style: str = "professional"
    
    # Optionen
    use_rag: bool = True
    generate_charts: bool = True
    match_assets: bool = True
    include_critique: bool = True
    export_pptx: bool = True
    
    # Advanced
    k: int = 5  # RAG top-k
    use_cases: List[str] = []
    custom_sections: List[str] = []


class AgentV3Response(BaseModel):
    """Response von Agent V3."""
    ok: bool
    run_id: str
    project_id: Optional[str] = None
    
    # Ergebnisse
    slides: List[Dict[str, Any]] = []
    slide_count: int = 0
    
    # Exports
    pptx_url: Optional[str] = None
    pdf_url: Optional[str] = None
    
    # Metriken
    quality_score: Optional[float] = None
    duration_s: float = 0
    
    # Details
    phases: Dict[str, Any] = {}
    warnings: List[str] = []


# ============================================
# HELPER FUNCTIONS
# ============================================

def _generate_run_id() -> str:
    """Generiert eine eindeutige Run-ID."""
    return f"v3-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(4).hex()}"


def _http_get(path: str, params: dict = None, timeout: int = 30) -> Optional[dict]:
    """HTTP GET Request an interne API."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _http_post(path: str, json_data: dict = None, timeout: int = 60) -> Optional[dict]:
    """HTTP POST Request an interne API."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json_data, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ============================================
# PHASE 1: BRIEFING ANALYSE
# ============================================

def phase_briefing(req: AgentV3Request) -> Dict[str, Any]:
    """
    Phase 1: Analysiert das Briefing und extrahiert Struktur.
    """
    result = {
        "topic": req.topic,
        "customer": req.customer_name,
        "industry": req.industry,
        "audience": req.audience,
        "deck_size": req.deck_size,
        "use_cases": req.use_cases or [],
        "keywords": [],
    }
    
    # Keywords aus Brief extrahieren
    brief_text = f"{req.topic} {req.brief} {req.industry}".lower()
    keyword_patterns = [
        "roi", "kosten", "einsparung", "effizienz", "automation",
        "digital", "transformation", "ki", "ai", "strategie",
        "marketing", "sales", "growth", "expansion"
    ]
    
    result["keywords"] = [kw for kw in keyword_patterns if kw in brief_text]
    
    # Use Cases aus Brief extrahieren wenn nicht angegeben
    if not result["use_cases"] and req.brief:
        # Einfache Extraktion - könnte mit LLM verbessert werden
        if HAS_LLM_CONTENT:
            # TODO: LLM-basierte Use-Case-Extraktion
            pass
    
    return result


# ============================================
# PHASE 2: KNOWLEDGE SEARCH (RAG)
# ============================================

def phase_knowledge(req: AgentV3Request, briefing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 2: Sucht relevantes Wissen aus Knowledge Base.
    """
    result = {
        "sources": [],
        "facts": [],
        "citations": [],
    }
    
    if not req.use_rag:
        return result
    
    # Knowledge Search
    query = f"{req.topic} {req.brief} {req.industry}"
    
    if knowledge_search:
        try:
            search_result = knowledge_search(query, limit=req.k, semantic=1)
            if search_result.get("ok"):
                for item in search_result.get("results", []):
                    result["sources"].append({
                        "path": item.get("path"),
                        "title": item.get("title") or Path(item.get("path", "")).stem,
                        "snippet": item.get("snippet", "")[:200]
                    })
                    if item.get("snippet"):
                        result["facts"].append(item["snippet"][:300])
        except Exception:
            pass
    
    # Fallback: HTTP API
    if not result["sources"]:
        resp = _http_get("/knowledge/search_semantic", {"q": query, "k": req.k})
        if resp:
            for item in resp.get("results", []) or resp.get("items", []):
                result["sources"].append({
                    "path": item.get("path"),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")[:200]
                })
    
    return result


# ============================================
# PHASE 3: STRUCTURE PLANNING
# ============================================

def phase_structure(req: AgentV3Request, briefing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 3: Plant die Deck-Struktur basierend auf Größe und Briefing.
    """
    size_config = DECK_SIZES.get(req.deck_size, DECK_SIZES["medium"])
    
    # Basis-Struktur aus Template Learner
    if HAS_TEMPLATE_LEARNER:
        suggestion = suggest_structure(
            deck_size=req.deck_size,
            topic=req.topic,
            industry=req.industry
        )
        if suggestion.get("ok"):
            return {
                "slides": suggestion.get("slides", []),
                "target_count": len(suggestion.get("slides", [])),
                "source": "template_learner"
            }
    
    # Fallback: Manuell aufbauen
    slides = []
    
    for module, config in sorted(SLIDE_MODULES.items(), key=lambda x: x[1]["order"]):
        # Prüfe ob Modul für diese Größe relevant
        min_size = config.get("min_size")
        if min_size:
            size_order = {"short": 0, "medium": 1, "large": 2}
            if size_order.get(req.deck_size, 1) < size_order.get(min_size, 1):
                continue
        
        # Füge Slide hinzu
        slides.append({
            "type": module,
            "title": _get_default_title(module, req.language),
            "order": config["order"]
        })
        
        # Expandable Slides (z.B. Use Cases)
        if config.get("expandable") and module == "use_cases":
            for i, uc in enumerate(briefing.get("use_cases", [])[:5]):
                slides.append({
                    "type": "use_case_detail",
                    "title": f"Use Case: {uc}",
                    "use_case": uc,
                    "order": config["order"] + 0.1 * (i + 1)
                })
    
    # Sortieren
    slides.sort(key=lambda x: x.get("order", 99))
    
    # Custom Sections einfügen
    if req.custom_sections:
        insert_idx = len(slides) - 2  # Vor "next_steps" und "contact"
        for section in req.custom_sections:
            slides.insert(insert_idx, {
                "type": "custom",
                "title": section,
                "order": 50
            })
            insert_idx += 1
    
    return {
        "slides": slides,
        "target_count": len(slides),
        "source": "rule_based"
    }


def _get_default_title(module: str, language: str = "de") -> str:
    """Gibt den Default-Titel für ein Modul zurück."""
    titles_de = {
        "title": "Strategiepräsentation",
        "agenda": "Agenda",
        "executive_summary": "Executive Summary",
        "problem": "Herausforderung",
        "solution": "Unser Ansatz",
        "use_cases": "Use Cases",
        "benefits": "Ihr Nutzen",
        "roi": "ROI & Business Case",
        "roadmap": "Roadmap",
        "team": "Unser Team",
        "competitive": "Marktpositionierung",
        "risks": "Risiken & Mitigation",
        "next_steps": "Nächste Schritte",
        "appendix": "Anhang",
        "contact": "Kontakt",
    }
    
    titles_en = {
        "title": "Strategy Presentation",
        "agenda": "Agenda",
        "executive_summary": "Executive Summary",
        "problem": "Challenge",
        "solution": "Our Approach",
        "use_cases": "Use Cases",
        "benefits": "Your Benefits",
        "roi": "ROI & Business Case",
        "roadmap": "Roadmap",
        "team": "Our Team",
        "competitive": "Market Position",
        "risks": "Risks & Mitigation",
        "next_steps": "Next Steps",
        "appendix": "Appendix",
        "contact": "Contact",
    }
    
    titles = titles_de if language == "de" else titles_en
    return titles.get(module, module.replace("_", " ").title())


# ============================================
# PHASE 4: CONTENT GENERATION
# ============================================

def phase_content(
    req: AgentV3Request,
    structure: Dict[str, Any],
    knowledge: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Phase 4: Generiert Content für jeden Slide via LLM.
    """
    slides = []
    facts_context = "\n".join(knowledge.get("facts", [])[:5])
    
    for slide_def in structure.get("slides", []):
        slide_type = slide_def.get("type", "content")
        title = slide_def.get("title", "")
        
        slide = {
            "type": slide_type,
            "title": title,
            "bullets": [],
            "notes": "",
            "layout_hint": _get_layout_hint(slide_type),
            "citations": [],
        }
        
        # LLM-basierte Content-Generierung
        if HAS_LLM_CONTENT:
            try:
                content = generate_slide_content(
                    slide_type=slide_type,
                    title=title,
                    brief=req.brief or req.topic,
                    context=facts_context,
                    num_bullets=_get_bullet_count(slide_type, req.deck_size),
                    language=req.language
                )
                
                slide["bullets"] = content.get("bullets", [])
                slide["notes"] = content.get("notes", "")
                
            except Exception as e:
                slide["notes"] = f"[Content-Generierung fehlgeschlagen: {str(e)}]"
                slide["bullets"] = [f"[Inhalt für {title}]"]
        else:
            # Fallback: Platzhalter
            slide["bullets"] = [f"• Punkt 1 zu {title}", f"• Punkt 2 zu {title}", f"• Punkt 3 zu {title}"]
            slide["notes"] = f"Erläuterungen zu {title}"
        
        # Citations aus Knowledge hinzufügen
        if knowledge.get("sources") and slide_type in ["executive_summary", "problem", "roi"]:
            slide["citations"] = [s["title"] for s in knowledge["sources"][:2]]
        
        slides.append(slide)
    
    return slides


def _get_layout_hint(slide_type: str) -> str:
    """Gibt den passenden Layout-Hint für einen Slide-Typ."""
    layouts = {
        "title": "Title",
        "agenda": "Title and Content",
        "executive_summary": "Title and Content",
        "problem": "Title and Content",
        "solution": "Title and Content",
        "use_cases": "Title and Content",
        "use_case_detail": "Two Content",
        "benefits": "Title and Content",
        "roi": "Title and Content",
        "roadmap": "Title and Content",
        "team": "Title and Content",
        "competitive": "Comparison",
        "risks": "Title and Content",
        "next_steps": "Title and Content",
        "appendix": "Title and Content",
        "contact": "Title and Content",
    }
    return layouts.get(slide_type, "Title and Content")


def _get_bullet_count(slide_type: str, deck_size: str) -> int:
    """Bestimmt die Anzahl Bullets basierend auf Slide-Typ und Deck-Größe."""
    base = {"short": 3, "medium": 4, "large": 5}
    
    # Einige Slide-Typen brauchen mehr/weniger
    if slide_type in ["title", "contact"]:
        return 1
    if slide_type == "agenda":
        return 6
    if slide_type == "executive_summary":
        return 4
    
    return base.get(deck_size, 4)


# ============================================
# PHASE 5: VISUALS (Charts & Assets)
# ============================================

def phase_visuals(
    req: AgentV3Request,
    slides: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Phase 5: Fügt Charts und Assets zu Slides hinzu.
    """
    # Charts generieren
    if req.generate_charts and HAS_CHART_GEN:
        for slide in slides:
            slide_type = slide.get("type", "")
            
            # Roadmap → Timeline Chart
            if slide_type == "roadmap":
                try:
                    result = create_timeline(
                        phases=[
                            {"name": "Phase 1", "duration": "2 Wo", "description": "Discovery"},
                            {"name": "Phase 2", "duration": "4 Wo", "description": "Pilot"},
                            {"name": "Phase 3", "duration": "8 Wo", "description": "Rollout"},
                            {"name": "Phase 4", "duration": "Ongoing", "description": "Optimierung"},
                        ],
                        title=""
                    )
                    if result.get("ok"):
                        slide["chart"] = result.get("path")
                        slide["has_chart"] = True
                except Exception:
                    pass
            
            # ROI → Bar Chart
            if slide_type == "roi":
                try:
                    result = create_bar_chart(
                        labels=["Kosten", "Einsparung Y1", "Einsparung Y2", "Einsparung Y3"],
                        values=[100, 40, 80, 120],
                        title="ROI Projektion",
                        horizontal=True
                    )
                    if result.get("ok"):
                        slide["chart"] = result.get("path")
                        slide["has_chart"] = True
                except Exception:
                    pass
    
    # Assets matchen
    if req.match_assets and HAS_ASSET_TAGGER:
        try:
            # Erst Uploads scannen
            scan_uploads_directory(UPLOADS_DIR)
            
            # Dann zu Slides matchen
            slides = match_assets_to_slides(slides)
        except Exception:
            pass
    
    return slides


# ============================================
# PHASE 6: CRITIQUE & QUALITY
# ============================================

def phase_critique(
    req: AgentV3Request,
    slides: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Phase 6: Qualitätsprüfung und Kritik.
    """
    result = {
        "score": 7.0,
        "issues": [],
        "suggestions": [],
    }
    
    if not req.include_critique:
        return result
    
    # Auto Quality Score
    if HAS_FEEDBACK:
        try:
            quality = get_quality_score(content={"slides": slides})
            result["score"] = quality.get("score", 7.0)
            result["suggestions"] = quality.get("suggestions", [])
        except Exception:
            pass
    
    # LLM-basierte Kritik (optional, kann langsam sein)
    if HAS_LLM_CONTENT and len(slides) <= 15:
        try:
            # Nur bei kleineren Decks
            content_summary = "\n".join([
                f"Slide: {s.get('title')} - Bullets: {len(s.get('bullets', []))}"
                for s in slides[:10]
            ])
            
            critique = generate_critique(content_summary, "presentation")
            result["issues"] = critique.get("risks", [])
            if critique.get("improvements"):
                result["suggestions"].extend(critique["improvements"][:3])
            
            # Score anpassen basierend auf Critique
            llm_score = critique.get("score", 7)
            result["score"] = round((result["score"] + llm_score) / 2, 1)
        except Exception:
            pass
    
    return result


# ============================================
# PHASE 7: RENDERING
# ============================================

def phase_render(
    req: AgentV3Request,
    slides: List[Dict[str, Any]],
    run_id: str
) -> Dict[str, Any]:
    """
    Phase 7: Rendert das Deck zu PPTX/PDF.
    """
    result = {
        "pptx_url": None,
        "pdf_url": None,
        "project_id": None,
    }
    
    if not req.export_pptx:
        return result
    
    # Projekt erstellen
    project_data = {
        "title": req.topic,
        "customer_name": req.customer_name,
        "topic": req.topic,
        "brief": req.brief,
        "outline": {
            "title": req.topic,
            "sections": slides
        },
        "meta": {
            "slide_plan": slides,
            "run_id": run_id,
        }
    }
    
    # Projekt speichern
    resp = _http_post("/projects/save", project_data)
    if resp and resp.get("project"):
        project_id = resp["project"].get("id")
        result["project_id"] = project_id
        
        # PPTX rendern
        if project_id:
            render_resp = _http_post(f"/pptx/render_from_project/{project_id}")
            if render_resp:
                pptx_path = render_resp.get("path") or render_resp.get("url")
                if pptx_path:
                    filename = Path(pptx_path).name
                    result["pptx_url"] = f"/exports/download/{filename}"
    
    return result


# ============================================
# MAIN ENDPOINT
# ============================================

@router.post("/run_v3", response_model=AgentV3Response)
async def run_v3(req: AgentV3Request, background_tasks: BackgroundTasks) -> AgentV3Response:
    """
    Agent V3: Vollständige Deck-Generierung.
    
    Orchestriert alle Services für professionelle Präsentationen:
    - LLM-basierte Content-Generierung
    - RAG Knowledge Integration
    - Chart & Asset Integration
    - Quality Critique
    - PPTX Export
    """
    run_id = _generate_run_id()
    t0 = time.time()
    warnings = []
    phases = {}
    
    # Service-Checks
    if not HAS_LLM_CONTENT:
        warnings.append("llm_content nicht verfügbar - Fallback auf Platzhalter")
    
    # === PHASE 1: Briefing ===
    t1 = time.time()
    briefing = phase_briefing(req)
    phases["briefing"] = {"duration_ms": int((time.time() - t1) * 1000)}
    
    # === PHASE 2: Knowledge ===
    t2 = time.time()
    knowledge = phase_knowledge(req, briefing)
    phases["knowledge"] = {
        "duration_ms": int((time.time() - t2) * 1000),
        "sources_found": len(knowledge.get("sources", []))
    }
    
    # === PHASE 3: Structure ===
    t3 = time.time()
    structure = phase_structure(req, briefing)
    phases["structure"] = {
        "duration_ms": int((time.time() - t3) * 1000),
        "planned_slides": len(structure.get("slides", []))
    }
    
    # === PHASE 4: Content ===
    t4 = time.time()
    slides = phase_content(req, structure, knowledge)
    phases["content"] = {
        "duration_ms": int((time.time() - t4) * 1000),
        "generated_slides": len(slides)
    }
    
    # === PHASE 5: Visuals ===
    t5 = time.time()
    slides = phase_visuals(req, slides)
    charts_count = sum(1 for s in slides if s.get("has_chart"))
    phases["visuals"] = {
        "duration_ms": int((time.time() - t5) * 1000),
        "charts_generated": charts_count
    }
    
    # === PHASE 6: Critique ===
    t6 = time.time()
    critique = phase_critique(req, slides)
    phases["critique"] = {
        "duration_ms": int((time.time() - t6) * 1000),
        "quality_score": critique.get("score")
    }
    warnings.extend(critique.get("issues", [])[:3])
    
    # === PHASE 7: Render ===
    t7 = time.time()
    render_result = phase_render(req, slides, run_id)
    phases["render"] = {
        "duration_ms": int((time.time() - t7) * 1000),
        "exported": render_result.get("pptx_url") is not None
    }
    
    # Response
    duration = round(time.time() - t0, 2)
    
    return AgentV3Response(
        ok=True,
        run_id=run_id,
        project_id=render_result.get("project_id"),
        slides=slides,
        slide_count=len(slides),
        pptx_url=render_result.get("pptx_url"),
        pdf_url=render_result.get("pdf_url"),
        quality_score=critique.get("score"),
        duration_s=duration,
        phases=phases,
        warnings=warnings
    )


# ============================================
# ZUSÄTZLICHE ENDPOINTS
# ============================================

@router.get("/v3/status")
def agent_v3_status():
    """Gibt den Status aller Services zurück."""
    status = {
        "version": "3.0",
        "services": {
            "llm_content": HAS_LLM_CONTENT,
            "asset_tagger": HAS_ASSET_TAGGER,
            "chart_generator": HAS_CHART_GEN,
            "template_learner": HAS_TEMPLATE_LEARNER,
            "feedback_loop": HAS_FEEDBACK,
        },
        "ollama": None,
    }
    
    # Ollama Status
    if HAS_LLM_CONTENT:
        try:
            status["ollama"] = check_ollama()
        except Exception:
            status["ollama"] = {"ok": False}
    
    return status


@router.get("/v3/deck_sizes")
def get_deck_sizes():
    """Gibt verfügbare Deck-Größen zurück."""
    return {
        "sizes": DECK_SIZES,
        "default": "medium"
    }


@router.post("/v3/preview")
async def preview_structure(req: AgentV3Request):
    """
    Gibt nur die geplante Struktur zurück (ohne Content-Generierung).
    Schneller für Vorschau/Planung.
    """
    briefing = phase_briefing(req)
    structure = phase_structure(req, briefing)
    
    return {
        "ok": True,
        "deck_size": req.deck_size,
        "slides": structure.get("slides", []),
        "slide_count": len(structure.get("slides", []))
    }


# ============================================
# REGISTER
# ============================================

def register_router(app):
    """Registriert den Agent V3 Router bei der App."""
    app.include_router(router)
