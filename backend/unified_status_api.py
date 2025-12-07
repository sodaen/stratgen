"""
Unified Status API - Ein Endpoint für alle Service-Status
Konsolidiert: agent, orchestrator, workers, knowledge, ollama, system
"""
from fastapi import APIRouter
from typing import Dict, Any
import httpx
import asyncio
import time
import psutil

router = APIRouter(tags=["unified-status"])


async def _fetch_internal(path: str, timeout: float = 3.0) -> Dict:
    """Fetch von internem Endpoint mit Timeout."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://127.0.0.1:8011{path}", timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"_fetch_internal {path} error: {e}")
    return {}


@router.get("/unified/status")
async def unified_status():
    """
    Zentraler Status-Endpoint für das gesamte System.
    Kombiniert alle relevanten Status-Infos in einer Response.
    """
    start = time.time()
    
    # Parallel alle Status abrufen
    results = await asyncio.gather(
        _fetch_internal("/agent/status"),
        _fetch_internal("/orchestrator/status"),
        _fetch_internal("/workers/status"),
        _fetch_internal("/knowledge/admin/status"),
        _fetch_internal("/ollama/status"),
        return_exceptions=True
    )
    
    agent = results[0] if isinstance(results[0], dict) else {}
    orchestrator = results[1] if isinstance(results[1], dict) else {}
    workers = results[2] if isinstance(results[2], dict) else {}
    knowledge = results[3] if isinstance(results[3], dict) else {}
    ollama = results[4] if isinstance(results[4], dict) else {}
    
    # System-Metriken direkt
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
    except:
        cpu_percent = 0
        mem = type('obj', (object,), {'percent': 0, 'used': 0, 'total': 1})()
        disk = type('obj', (object,), {'percent': 0, 'free': 0, 'total': 1})()
    
    # FIX: Workers Response richtig interpretieren
    # workers endpoint gibt: {"ok": true, "celery_available": true, "worker_count": 1, ...}
    celery_available = workers.get("celery_available", False) or workers.get("ok", False)
    worker_count = workers.get("worker_count", 0)
    
    # Konsolidierte Response
    return {
        "ok": True,
        "timestamp": time.time(),
        "response_ms": round((time.time() - start) * 1000, 1),
        
        # Core Services
        "services": {
            "api": {
                "status": "online",
                "response_ms": round((time.time() - start) * 1000, 1)
            },
            "ollama": {
                "status": "online" if agent.get("ollama", {}).get("ok") or ollama.get("ok") else "offline",
                "model": agent.get("ollama", {}).get("model", "unknown"),
                "model_loaded": agent.get("ollama", {}).get("model_loaded", False)
            },
            "qdrant": {
                "status": "online" if knowledge.get("ok") else "offline",
                "collections": len(knowledge.get("collections", {})),
                "total_chunks": knowledge.get("total_chunks", 0)
            },
            "redis": {
                # Redis ist verfügbar wenn Celery verfügbar ist
                "status": "online" if celery_available else "offline"
            },
            "celery": {
                "status": "online" if worker_count > 0 else "offline",
                "worker_count": worker_count,
                "queues": workers.get("queues", {})
            }
        },
        
        # Features (from orchestrator)
        "features": orchestrator.get("features", {}),
        "features_available": orchestrator.get("features_available", 0),
        "features_total": orchestrator.get("features_total", 0),
        
        # Agent Info
        "agent": {
            "version": agent.get("version", "unknown"),
            "intelligence": agent.get("features", {}).get("agent_intelligence", False)
        },
        
        # Knowledge Stats
        "knowledge": {
            "total_chunks": knowledge.get("total_chunks", 0),
            "collections": knowledge.get("collections", {}),
            "metrics": knowledge.get("metrics", {})
        },
        
        # System Resources
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_total_gb": round(mem.total / (1024**3), 1),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 1)
        },
        
        # Raw workers data for debugging
        "workers": workers
    }


@router.get("/unified/health")
async def unified_health():
    """Schneller Health-Check für alle Services."""
    checks = {}
    
    # API selbst - immer online wenn dieser Endpoint antwortet
    checks["api"] = True
    
    # Ollama
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags", timeout=2)
            checks["ollama"] = resp.status_code == 200
    except:
        checks["ollama"] = False
    
    # Qdrant
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:6333/collections", timeout=2)
            checks["qdrant"] = resp.status_code == 200
    except:
        checks["qdrant"] = False
    
    # Redis/Celery (via workers endpoint)
    try:
        workers = await _fetch_internal("/workers/status", timeout=2)
        checks["redis"] = workers.get("celery_available", False) or workers.get("ok", False)
        checks["celery"] = workers.get("worker_count", 0) > 0
    except:
        checks["redis"] = False
        checks["celery"] = False
    
    all_ok = all(checks.values())
    
    return {
        "ok": all_ok,
        "checks": checks,
        "summary": f"{sum(checks.values())}/{len(checks)} services online"
    }
