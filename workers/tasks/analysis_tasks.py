# -*- coding: utf-8 -*-
"""
workers/tasks/analysis_tasks.py
===============================
Analysis Tasks für Celery Worker

Diese Tasks sind CPU-intensiv und können auf
mehrere CPU-Rechner verteilt werden.

Tasks:
- analyze_briefing: Briefing-Analyse
- analyze_dna: Template DNA Analyse
- analyze_voice: Brand Voice Analyse
- check_consistency: Konsistenzprüfung
- orchestrate_analysis: Vollständige orchestrierte Analyse
"""
from celery import shared_task, chain, group
from typing import Dict, Any, List, Optional
import time

# ============================================
# SERVICE IMPORTS (Lazy)
# ============================================

def get_briefing_analyzer():
    try:
        from services.briefing_analyzer import analyze
        return analyze
    except ImportError:
        return None

def get_dna_analyzer():
    try:
        from services.slide_dna_analyzer import get_optimal_structure, extract_slide_dna
        return get_optimal_structure, extract_slide_dna
    except ImportError:
        return None, None

def get_voice_extractor():
    try:
        from services.brand_voice_extractor import get_writing_guidelines
        return get_writing_guidelines
    except ImportError:
        return None

def get_story_engine():
    try:
        from services.story_engine import create_story_structure
        return create_story_structure
    except ImportError:
        return None

def get_semantic_matcher():
    try:
        from services.semantic_slide_matcher import get_slide_suggestions
        return get_slide_suggestions
    except ImportError:
        return None

def get_argument_engine():
    try:
        from services.argument_engine import check_deck_consistency, generate_objections
        return check_deck_consistency, generate_objections
    except ImportError:
        return None, None

def get_orchestrator():
    try:
        from services.feature_orchestrator import orchestrator
        return orchestrator
    except ImportError:
        return None


# ============================================
# TASKS
# ============================================

@shared_task(
    bind=True,
    name="analysis.briefing",
    max_retries=2
)
def analyze_briefing(
    self,
    brief: str,
    topic: str,
    industry: str = "",
    customer_name: str = ""
) -> Dict[str, Any]:
    """
    Analysiert ein Briefing.
    
    Returns:
        Briefing-Analyse mit Quality Score, Intent, etc.
    """
    analyze = get_briefing_analyzer()
    
    if analyze is None:
        return {"ok": False, "error": "Briefing Analyzer nicht verfügbar"}
    
    try:
        result = analyze(brief, topic, industry, customer_name)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.dna",
    max_retries=2
)
def analyze_dna(
    self,
    topic: str,
    deck_size: str = "medium",
    industry: str = ""
) -> Dict[str, Any]:
    """
    Analysiert Template DNA für optimale Struktur.
    
    Returns:
        Optimale Struktur basierend auf Templates.
    """
    get_optimal, extract_dna = get_dna_analyzer()
    
    if get_optimal is None:
        return {"ok": False, "error": "DNA Analyzer nicht verfügbar"}
    
    try:
        result = get_optimal(topic, deck_size, industry)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.voice",
    max_retries=2
)
def analyze_voice(
    self,
    profile_name: str = "default"
) -> Dict[str, Any]:
    """
    Holt Brand Voice Guidelines.
    
    Returns:
        Writing Guidelines.
    """
    get_guidelines = get_voice_extractor()
    
    if get_guidelines is None:
        return {"ok": False, "error": "Voice Extractor nicht verfügbar"}
    
    try:
        result = get_guidelines(profile_name)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.story",
    max_retries=2
)
def analyze_story(
    self,
    brief: str,
    topic: str,
    audience: str = "",
    deck_size: str = "medium"
) -> Dict[str, Any]:
    """
    Analysiert Story-Framework.
    
    Returns:
        Empfohlenes Framework und Struktur.
    """
    create_story = get_story_engine()
    
    if create_story is None:
        return {"ok": False, "error": "Story Engine nicht verfügbar"}
    
    try:
        result = create_story(brief, topic, audience, "", deck_size)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.semantic",
    max_retries=2
)
def find_similar_slides(
    self,
    query: str,
    slide_type: str = "",
    industry: str = "",
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Findet ähnliche Slides aus Templates.
    
    Returns:
        Liste ähnlicher Slides.
    """
    get_suggestions = get_semantic_matcher()
    
    if get_suggestions is None:
        return {"ok": False, "error": "Semantic Matcher nicht verfügbar"}
    
    try:
        result = get_suggestions(query, slide_type, industry)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.consistency",
    max_retries=2
)
def check_consistency(
    self,
    slides: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Prüft Deck auf Konsistenz.
    
    Returns:
        Consistency Score und Issues.
    """
    check_deck, generate_obj = get_argument_engine()
    
    if check_deck is None:
        return {"ok": False, "error": "Argument Engine nicht verfügbar"}
    
    try:
        result = check_deck(slides)
        result["task_id"] = self.request.id
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.objections",
    max_retries=2
)
def generate_objections_task(
    self,
    topic: str,
    industry: str = ""
) -> Dict[str, Any]:
    """
    Generiert potenzielle Einwände.
    
    Returns:
        Liste von Einwänden mit Counter-Arguments.
    """
    check_deck, generate_obj = get_argument_engine()
    
    if generate_obj is None:
        return {"ok": False, "error": "Argument Engine nicht verfügbar"}
    
    try:
        from dataclasses import asdict
        objections = generate_obj(topic, industry)
        
        return {
            "ok": True,
            "objections": [asdict(o) for o in objections],
            "task_id": self.request.id
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="analysis.orchestrate",
    max_retries=2,
    time_limit=120  # 2 Minuten max
)
def orchestrate_analysis(
    self,
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    audience: str = "",
    deck_size: str = "medium"
) -> Dict[str, Any]:
    """
    Führt vollständige orchestrierte Analyse durch.
    
    Dies ist der Haupt-Task der alle Features kombiniert.
    
    Returns:
        Vollständige Analyse mit allen Features.
    """
    orch = get_orchestrator()
    
    if orch is None:
        return {"ok": False, "error": "Orchestrator nicht verfügbar"}
    
    start_time = time.time()
    
    try:
        from dataclasses import asdict
        
        analysis = orch.analyze(
            topic=topic,
            brief=brief,
            customer_name=customer_name,
            industry=industry,
            audience=audience,
            deck_size=deck_size
        )
        
        elapsed = time.time() - start_time
        
        return {
            "ok": True,
            "analysis": asdict(analysis),
            "features_used": analysis.features_used,
            "elapsed_ms": int(elapsed * 1000),
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


# ============================================
# PERIODIC TASKS
# ============================================

@shared_task(name="analysis.health_check")
def health_check() -> Dict[str, Any]:
    """
    Periodischer Health Check.
    """
    services = {
        "briefing_analyzer": get_briefing_analyzer() is not None,
        "dna_analyzer": get_dna_analyzer()[0] is not None,
        "voice_extractor": get_voice_extractor() is not None,
        "story_engine": get_story_engine() is not None,
        "semantic_matcher": get_semantic_matcher() is not None,
        "argument_engine": get_argument_engine()[0] is not None,
        "orchestrator": get_orchestrator() is not None
    }
    
    available = sum(1 for v in services.values() if v)
    
    return {
        "ok": True,
        "timestamp": time.time(),
        "services_available": available,
        "services_total": len(services),
        "services": services
    }


@shared_task(name="analysis.cleanup_old_results")
def cleanup_old_results() -> Dict[str, Any]:
    """
    Räumt alte Task-Results auf.
    """
    # Redis cleanup wird automatisch durch result_expires gemacht
    return {
        "ok": True,
        "timestamp": time.time(),
        "message": "Cleanup completed"
    }


# ============================================
# COMPOSITE TASKS (Chains/Groups)
# ============================================

def create_full_analysis_workflow(
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    audience: str = "",
    deck_size: str = "medium"
):
    """
    Erstellt einen Workflow für parallele Analyse.
    
    Nutzt Celery Groups für parallele Ausführung.
    """
    # Diese Tasks laufen parallel
    parallel_tasks = group(
        analyze_briefing.s(brief, topic, industry, customer_name),
        analyze_dna.s(topic, deck_size, industry),
        analyze_voice.s("default"),
        analyze_story.s(brief, topic, audience, deck_size),
        find_similar_slides.s(f"{topic} {brief[:100]}", "", industry, 5)
    )
    
    return parallel_tasks
