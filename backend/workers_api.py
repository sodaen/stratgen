# -*- coding: utf-8 -*-
"""
backend/workers_api.py
======================
API Endpoints für Worker-Management und Task-Ausführung

Endpoints:
- /workers/status - Worker Status
- /workers/queues - Queue Längen
- /workers/tasks/submit - Task einreichen
- /workers/tasks/{id} - Task Status
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

router = APIRouter(prefix="/workers", tags=["Workers"])

# ============================================
# CELERY IMPORTS
# ============================================

CELERY_AVAILABLE = False
celery_app = None

try:
    from workers.celery_app import app as celery_app, get_queue_lengths, get_active_workers
    CELERY_AVAILABLE = True
except ImportError as e:
    print(f"Celery nicht verfügbar: {e}")


# ============================================
# MODELS
# ============================================

class TaskSubmitRequest(BaseModel):
    task_type: str  # llm, analysis, generation, export
    task_name: str  # z.B. "briefing", "slide", "pptx"
    params: Dict[str, Any]
    priority: int = 5  # 1-10, höher = wichtiger
    queue: Optional[str] = None  # Optional: spezifische Queue


class FullPipelineRequest(BaseModel):
    topic: str
    brief: str
    customer_name: str = ""
    industry: str = ""
    audience: str = ""
    deck_size: str = "medium"
    export_formats: List[str] = ["pptx", "json"]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
def workers_status():
    """
    Gibt den Status aller Worker zurück.
    """
    if not CELERY_AVAILABLE:
        return {
            "ok": False,
            "celery_available": False,
            "message": "Celery nicht installiert. Starte mit: pip install celery redis"
        }
    
    try:
        workers = get_active_workers()
        queues = get_queue_lengths()
        
        return {
            "ok": True,
            "celery_available": True,
            "workers": workers,
            "worker_count": len(workers),
            "queues": queues,
            "total_queued": sum(v for v in queues.values() if v >= 0)
        }
    except Exception as e:
        return {
            "ok": False,
            "celery_available": True,
            "error": str(e),
            "message": "Celery verfügbar aber keine Worker aktiv. Starte mit: celery -A workers.celery_app worker"
        }


@router.get("/queues")
def queue_status():
    """
    Gibt die Länge aller Queues zurück.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(503, "Celery nicht verfügbar")
    
    try:
        return {
            "ok": True,
            "queues": get_queue_lengths()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/tasks/submit")
def submit_task(req: TaskSubmitRequest):
    """
    Reicht einen Task zur Ausführung ein.
    
    Task Types:
    - llm: LLM-Tasks (generate_content, generate_embedding)
    - analysis: Analyse-Tasks (briefing, dna, voice, story)
    - generation: Generierungs-Tasks (slide, deck)
    - export: Export-Tasks (pptx, html, pdf, json)
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(503, "Celery nicht verfügbar")
    
    # Task-Mapping
    task_map = {
        "llm": {
            "generate_content": "llm.generate_content",
            "generate_embedding": "llm.generate_embedding",
            "generate_slide_content": "llm.generate_slide_content",
            "batch_generate": "llm.batch_generate",
        },
        "analysis": {
            "briefing": "analysis.briefing",
            "dna": "analysis.dna",
            "voice": "analysis.voice",
            "story": "analysis.story",
            "semantic": "analysis.semantic",
            "consistency": "analysis.consistency",
            "orchestrate": "analysis.orchestrate",
            "objections": "analysis.objections",
        },
        "generation": {
            "slide": "generation.slide",
            "deck": "generation.deck",
            "deck_parallel": "generation.deck_parallel",
            "full_pipeline": "generation.full_pipeline",
        },
        "export": {
            "pptx": "export.pptx",
            "html": "export.html",
            "pdf": "export.pdf",
            "markdown": "export.markdown",
            "json": "export.json",
            "multi": "export.multi",
        }
    }
    
    # Task finden
    task_type_map = task_map.get(req.task_type)
    if not task_type_map:
        raise HTTPException(400, f"Unbekannter Task-Typ: {req.task_type}")
    
    task_name = task_type_map.get(req.task_name)
    if not task_name:
        raise HTTPException(400, f"Unbekannter Task: {req.task_name}")
    
    # Queue bestimmen
    queue = req.queue or req.task_type
    if req.priority >= 8:
        queue = f"{queue}.high"
    
    try:
        # Task einreichen
        result = celery_app.send_task(
            task_name,
            kwargs=req.params,
            queue=queue,
            priority=req.priority
        )
        
        return {
            "ok": True,
            "task_id": result.id,
            "task_name": task_name,
            "queue": queue,
            "status": "PENDING"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Task konnte nicht eingereicht werden: {e}")


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Gibt den Status eines Tasks zurück.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(503, "Celery nicht verfügbar")
    
    try:
        result = celery_app.AsyncResult(task_id)
        
        response = {
            "ok": True,
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.result) if result.result else "Unknown error"
        
        return response
        
    except Exception as e:
        return {"ok": False, "task_id": task_id, "error": str(e)}


@router.delete("/tasks/{task_id}")
def cancel_task(task_id: str):
    """
    Bricht einen Task ab.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(503, "Celery nicht verfügbar")
    
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"ok": True, "task_id": task_id, "status": "CANCELLED"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/pipeline/full")
def submit_full_pipeline(req: FullPipelineRequest):
    """
    Startet eine vollständige Pipeline als Background-Task.
    
    Führt aus:
    1. Orchestrierte Analyse
    2. Deck-Generierung
    3. Multi-Format Export
    """
    if not CELERY_AVAILABLE:
        # Fallback: Synchrone Ausführung
        return _run_pipeline_sync(req)
    
    try:
        # Task einreichen
        result = celery_app.send_task(
            "generation.full_pipeline",
            kwargs={
                "topic": req.topic,
                "brief": req.brief,
                "customer_name": req.customer_name,
                "industry": req.industry,
                "audience": req.audience,
                "deck_size": req.deck_size
            },
            queue="generation"
        )
        
        return {
            "ok": True,
            "task_id": result.id,
            "status": "SUBMITTED",
            "status_url": f"/workers/tasks/{result.id}",
            "message": "Pipeline gestartet. Prüfe Status unter status_url."
        }
        
    except Exception as e:
        raise HTTPException(500, f"Pipeline konnte nicht gestartet werden: {e}")


def _run_pipeline_sync(req: FullPipelineRequest) -> Dict[str, Any]:
    """
    Synchrone Ausführung wenn Celery nicht verfügbar.
    """
    try:
        from services.feature_orchestrator import orchestrate_analysis
        
        # Analyse
        analysis = orchestrate_analysis(
            topic=req.topic,
            brief=req.brief,
            customer_name=req.customer_name,
            industry=req.industry,
            audience=req.audience,
            deck_size=req.deck_size
        )
        
        return {
            "ok": True,
            "mode": "sync",
            "analysis": analysis,
            "message": "Synchrone Ausführung (Celery nicht verfügbar)"
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================
# HEALTH & MONITORING
# ============================================

@router.get("/health")
def workers_health():
    """
    Health Check für Worker-System.
    """
    health = {
        "celery_available": CELERY_AVAILABLE,
        "timestamp": time.time()
    }
    
    if CELERY_AVAILABLE:
        try:
            workers = get_active_workers()
            health["workers_active"] = len(workers) > 0
            health["worker_count"] = len(workers)
        except Exception:
            health["workers_active"] = False
            health["worker_count"] = 0
    
    health["ok"] = health.get("workers_active", False) or not CELERY_AVAILABLE
    
    return health


@router.get("/inspect")
def inspect_workers():
    """
    Detaillierte Worker-Inspektion.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(503, "Celery nicht verfügbar")
    
    try:
        inspect = celery_app.control.inspect()
        
        return {
            "ok": True,
            "active": inspect.active() or {},
            "scheduled": inspect.scheduled() or {},
            "reserved": inspect.reserved() or {},
            "stats": inspect.stats() or {}
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
