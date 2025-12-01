# -*- coding: utf-8 -*-
"""
workers/tasks/generation_tasks.py
=================================
Generation Tasks für Celery Worker

Tasks für Slide- und Deck-Generierung.

Tasks:
- generate_slide: Einzelnen Slide generieren
- generate_deck: Komplettes Deck generieren
- generate_deck_streaming: Deck mit Progress-Updates
"""
from celery import shared_task, chord, group, chain
from typing import Dict, Any, List, Optional
import time
import json

# ============================================
# IMPORTS
# ============================================

def get_live_generator():
    try:
        from services.live_generator import live_generator, LiveGenerationRequest
        return live_generator, LiveGenerationRequest
    except ImportError:
        return None, None


# ============================================
# TASKS
# ============================================

@shared_task(
    bind=True,
    name="generation.slide",
    max_retries=3,
    default_retry_delay=5
)
def generate_slide(
    self,
    slide_type: str,
    title: str,
    topic: str,
    brief: str,
    index: int = 0,
    voice_guidelines: Optional[Dict] = None,
    similar_slides: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Generiert einen einzelnen Slide.
    
    Args:
        slide_type: Typ des Slides
        title: Slide-Titel
        topic: Hauptthema
        brief: Briefing
        index: Slide-Index
        voice_guidelines: Schreibstil
        similar_slides: Ähnliche Slides als Referenz
    
    Returns:
        Generierter Slide
    """
    # Import LLM Task
    from workers.tasks.llm_tasks import generate_slide_content
    
    start_time = time.time()
    
    # Referenz-Bullets aus ähnlichen Slides
    reference_hints = ""
    if similar_slides:
        for s in similar_slides[:2]:
            if s.get("type") == slide_type:
                preview = s.get("preview", "")[:100]
                reference_hints += f"\nReferenz: {preview}"
    
    # Context aufbauen
    context = {
        "topic": topic,
        "brief": brief[:300],
        "slide_type": slide_type,
        "index": index
    }
    
    if reference_hints:
        context["reference"] = reference_hints
    
    try:
        # Rufe LLM Task auf (synchron innerhalb dieses Tasks)
        result = generate_slide_content(
            slide_type=slide_type,
            title=title,
            topic=topic,
            brief=brief,
            context=context,
            voice_guidelines=voice_guidelines
        )
        
        elapsed = time.time() - start_time
        
        if result.get("ok"):
            return {
                "ok": True,
                "slide": {
                    "type": slide_type,
                    "title": title,
                    "bullets": result.get("bullets", []),
                    "notes": f"Slide {index + 1}: {slide_type}",
                    "layout_hint": "Title and Content"
                },
                "index": index,
                "elapsed_ms": int(elapsed * 1000),
                "task_id": self.request.id
            }
        else:
            return {
                "ok": False,
                "error": result.get("error", "Generation failed"),
                "index": index,
                "task_id": self.request.id
            }
            
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "index": index,
            "task_id": self.request.id
        }


@shared_task(
    bind=True,
    name="generation.deck",
    max_retries=2,
    time_limit=300  # 5 Minuten
)
def generate_deck(
    self,
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    deck_size: str = "medium",
    structure: Optional[List[Dict]] = None,
    voice_guidelines: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generiert ein komplettes Deck.
    
    Args:
        topic: Hauptthema
        brief: Briefing
        customer_name: Kundenname
        industry: Branche
        deck_size: Größe (short, medium, long)
        structure: Vordefinierte Struktur
        voice_guidelines: Schreibstil
    
    Returns:
        Komplettes Deck mit allen Slides
    """
    start_time = time.time()
    
    # Standard-Struktur wenn keine vorgegeben
    if not structure:
        size_map = {"short": 5, "medium": 8, "long": 12}
        slide_count = size_map.get(deck_size, 8)
        
        structure = [
            {"type": "title", "title": topic},
            {"type": "executive_summary", "title": "Executive Summary"},
            {"type": "problem", "title": "Herausforderung"},
            {"type": "solution", "title": "Unser Ansatz"},
            {"type": "benefits", "title": "Ihr Nutzen"},
            {"type": "roadmap", "title": "Roadmap"},
            {"type": "roi", "title": "Business Case"},
            {"type": "next_steps", "title": "Nächste Schritte"},
        ][:slide_count]
    
    slides = []
    errors = []
    
    # Slides sequenziell generieren
    for idx, slide_plan in enumerate(structure):
        try:
            result = generate_slide(
                slide_type=slide_plan.get("type", "content"),
                title=slide_plan.get("title", f"Slide {idx + 1}"),
                topic=topic,
                brief=brief,
                index=idx,
                voice_guidelines=voice_guidelines
            )
            
            if result.get("ok"):
                slides.append(result.get("slide"))
            else:
                errors.append({
                    "index": idx,
                    "error": result.get("error", "Unknown error")
                })
                # Fallback Slide
                slides.append({
                    "type": slide_plan.get("type", "content"),
                    "title": slide_plan.get("title", f"Slide {idx + 1}"),
                    "bullets": [f"Content für {topic}"],
                    "notes": "",
                    "layout_hint": "Title and Content"
                })
                
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})
    
    elapsed = time.time() - start_time
    
    return {
        "ok": len(errors) < len(structure) / 2,  # OK wenn weniger als 50% Fehler
        "slides": slides,
        "total_slides": len(slides),
        "errors": errors,
        "error_count": len(errors),
        "elapsed_ms": int(elapsed * 1000),
        "task_id": self.request.id
    }


@shared_task(
    bind=True,
    name="generation.deck_parallel",
    max_retries=2,
    time_limit=300
)
def generate_deck_parallel(
    self,
    topic: str,
    brief: str,
    structure: List[Dict],
    voice_guidelines: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generiert Deck mit paralleler Slide-Generierung.
    
    Nutzt Celery Group für parallele Ausführung.
    """
    start_time = time.time()
    
    # Erstelle Gruppe von Slide-Tasks
    slide_tasks = group([
        generate_slide.s(
            slide_type=s.get("type", "content"),
            title=s.get("title", f"Slide {i + 1}"),
            topic=topic,
            brief=brief,
            index=i,
            voice_guidelines=voice_guidelines
        )
        for i, s in enumerate(structure)
    ])
    
    # Führe parallel aus
    result = slide_tasks.apply_async()
    
    # Warte auf Ergebnisse (mit Timeout)
    try:
        results = result.get(timeout=240)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Parallel generation timeout: {e}",
            "task_id": self.request.id
        }
    
    # Sammle Slides
    slides = []
    errors = []
    
    for r in results:
        if r.get("ok"):
            slides.append(r.get("slide"))
        else:
            errors.append({
                "index": r.get("index", -1),
                "error": r.get("error", "Unknown")
            })
    
    # Sortiere nach Index
    slides.sort(key=lambda s: structure.index(
        next((x for x in structure if x.get("type") == s.get("type")), structure[0])
    ) if s else 999)
    
    elapsed = time.time() - start_time
    
    return {
        "ok": len(slides) > 0,
        "slides": slides,
        "total_slides": len(slides),
        "errors": errors,
        "parallel": True,
        "elapsed_ms": int(elapsed * 1000),
        "task_id": self.request.id
    }


@shared_task(
    bind=True,
    name="generation.full_pipeline",
    max_retries=1,
    time_limit=600  # 10 Minuten
)
def generate_full_pipeline(
    self,
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    audience: str = "",
    deck_size: str = "medium"
) -> Dict[str, Any]:
    """
    Führt vollständige Pipeline durch:
    1. Analyse (orchestriert)
    2. Struktur bestimmen
    3. Slides generieren
    4. QA durchführen
    
    Returns:
        Komplettes Deck mit Analyse und QA
    """
    from workers.tasks.analysis_tasks import orchestrate_analysis, check_consistency
    
    start_time = time.time()
    results = {"phases": {}}
    
    # Phase 1: Analyse
    try:
        analysis_result = orchestrate_analysis(
            topic=topic,
            brief=brief,
            customer_name=customer_name,
            industry=industry,
            audience=audience,
            deck_size=deck_size
        )
        results["phases"]["analysis"] = {
            "ok": analysis_result.get("ok", False),
            "elapsed_ms": analysis_result.get("elapsed_ms", 0)
        }
        
        analysis = analysis_result.get("analysis", {})
        
    except Exception as e:
        results["phases"]["analysis"] = {"ok": False, "error": str(e)}
        analysis = {}
    
    # Phase 2: Struktur
    structure = analysis.get("recommended_structure", [])
    if not structure:
        size_map = {"short": 5, "medium": 8, "long": 12}
        structure = [
            {"type": "title", "title": topic},
            {"type": "problem", "title": "Herausforderung"},
            {"type": "solution", "title": "Lösung"},
            {"type": "benefits", "title": "Nutzen"},
            {"type": "next_steps", "title": "Nächste Schritte"},
        ][:size_map.get(deck_size, 5)]
    
    results["phases"]["structure"] = {
        "ok": True,
        "slide_count": len(structure)
    }
    
    # Phase 3: Generierung
    try:
        voice = analysis.get("writing_guidelines", {})
        
        gen_result = generate_deck(
            topic=topic,
            brief=brief,
            customer_name=customer_name,
            industry=industry,
            deck_size=deck_size,
            structure=structure,
            voice_guidelines=voice
        )
        
        results["phases"]["generation"] = {
            "ok": gen_result.get("ok", False),
            "slides": len(gen_result.get("slides", [])),
            "elapsed_ms": gen_result.get("elapsed_ms", 0)
        }
        
        slides = gen_result.get("slides", [])
        
    except Exception as e:
        results["phases"]["generation"] = {"ok": False, "error": str(e)}
        slides = []
    
    # Phase 4: QA
    if slides:
        try:
            qa_result = check_consistency(slides)
            results["phases"]["qa"] = {
                "ok": qa_result.get("ok", False),
                "consistency_score": qa_result.get("consistency_score", 0)
            }
        except Exception as e:
            results["phases"]["qa"] = {"ok": False, "error": str(e)}
    
    elapsed = time.time() - start_time
    
    return {
        "ok": len(slides) > 0,
        "slides": slides,
        "analysis": analysis,
        "phases": results["phases"],
        "total_elapsed_ms": int(elapsed * 1000),
        "task_id": self.request.id
    }
