"""
Admin Metrics API für Stratgen.
Sammelt System-Metriken, Lern-Aktivitäten und Performance-Daten.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import psutil
import json
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
METRICS_FILE = DATA_ROOT / "metrics" / "system_metrics.json"


def _load_metrics_history() -> List[Dict]:
    """Lädt Metriken-Historie."""
    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def _save_metrics(metrics: Dict):
    """Speichert aktuelle Metriken."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    history = _load_metrics_history()
    history.append({**metrics, "timestamp": datetime.now().isoformat()})
    
    # Behalte nur letzte 1000 Einträge
    history = history[-1000:]
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(history, f)


@router.get("/metrics")
async def get_system_metrics():
    """Aktuelle System-Metriken."""
    try:
        # CPU & Memory
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Prozess-spezifisch
        process = psutil.Process()
        process_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Qdrant Stats
        qdrant_stats = {}
        try:
            from services.unified_knowledge import get_stats
            uk_stats = get_stats()
            qdrant_stats = uk_stats.get("collections", {})
        except:
            pass
        
        # Session Stats
        sessions_dir = DATA_ROOT / "sessions"
        session_count = len(list(sessions_dir.glob("*"))) if sessions_dir.exists() else 0
        
        # Export Stats
        exports_dir = DATA_ROOT / "exports"
        export_count = len(list(exports_dir.glob("*.pptx"))) if exports_dir.exists() else 0
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_free_gb": disk.free / (1024**3)
            },
            "process": {
                "memory_mb": round(process_memory, 1),
                "threads": process.num_threads()
            },
            "knowledge": {
                "collections": qdrant_stats,
                "total_chunks": sum(c.get("points", 0) for c in qdrant_stats.values())
            },
            "activity": {
                "sessions": session_count,
                "exports": export_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Speichere für Historie
        _save_metrics(metrics)
        
        return {"ok": True, **metrics}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/metrics/history")
async def get_metrics_history(hours: int = 24):
    """Metriken-Historie der letzten X Stunden."""
    try:
        history = _load_metrics_history()
        
        # Filtere nach Zeitraum
        cutoff = datetime.now() - timedelta(hours=hours)
        filtered = [
            m for m in history 
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        return {
            "ok": True,
            "count": len(filtered),
            "hours": hours,
            "metrics": filtered
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/learning/stats")
async def get_learning_stats():
    """Statistiken über Lern-Aktivitäten."""
    try:
        stats = {
            "knowledge_files": 0,
            "templates_learned": 0,
            "last_learning": None,
            "learning_errors": 0
        }
        
        # Knowledge Files
        knowledge_dir = DATA_ROOT / "knowledge"
        if knowledge_dir.exists():
            stats["knowledge_files"] = len([
                f for f in knowledge_dir.rglob("*") 
                if f.is_file() and f.suffix in ('.txt', '.md', '.pdf', '.docx')
            ])
        
        # Template Stats
        try:
            from services.template_learner import get_stats
            template_stats = get_stats()
            stats["templates_learned"] = template_stats.get("templates_learned", 0)
            stats["last_learning"] = template_stats.get("last_scan")
        except:
            pass
        
        # Auto-Learn DB
        autolearn_db = DATA_ROOT / "autolearn.sqlite"
        if autolearn_db.exists():
            import sqlite3
            try:
                con = sqlite3.connect(str(autolearn_db))
                cur = con.cursor()
                cur.execute("SELECT COUNT(*) FROM learned_files WHERE status='error'")
                stats["learning_errors"] = cur.fetchone()[0]
                con.close()
            except:
                pass
        
        return {"ok": True, **stats}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/generation/stats")
async def get_generation_stats():
    """Statistiken über Generierungs-Aktivitäten."""
    try:
        # Zähle Sessions und Slides
        sessions_dir = DATA_ROOT / "sessions"
        
        total_sessions = 0
        total_slides = 0
        recent_sessions = []
        
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    total_sessions += 1
                    
                    # Zähle Slides
                    slides_file = session_dir / "slides.json"
                    if slides_file.exists():
                        try:
                            with open(slides_file) as f:
                                slides = json.load(f)
                                total_slides += len(slides) if isinstance(slides, list) else 0
                        except:
                            pass
                    
                    # Sammle recent sessions
                    meta_file = session_dir / "meta.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file) as f:
                                meta = json.load(f)
                                recent_sessions.append({
                                    "id": session_dir.name,
                                    "title": meta.get("title", "Untitled"),
                                    "created": meta.get("created_at"),
                                    "slides": meta.get("slide_count", 0)
                                })
                        except:
                            pass
        
        # Sortiere nach Datum
        recent_sessions.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return {
            "ok": True,
            "total_sessions": total_sessions,
            "total_slides": total_slides,
            "avg_slides_per_session": round(total_slides / max(total_sessions, 1), 1),
            "recent_sessions": recent_sessions[:10]
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/services/status")
async def get_services_status():
    """Status aller Backend-Services."""
    services = {}
    
    # Qdrant
    try:
        import httpx
        r = httpx.get("http://localhost:6333/collections", timeout=2)
        services["qdrant"] = {"status": "online", "collections": len(r.json().get("result", {}).get("collections", []))}
    except:
        services["qdrant"] = {"status": "offline"}
    
    # Ollama
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        models = r.json().get("models", [])
        services["ollama"] = {"status": "online", "models": len(models)}
    except:
        services["ollama"] = {"status": "offline"}
    
    # Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        services["redis"] = {"status": "online"}
    except:
        services["redis"] = {"status": "offline"}
    
    # Celery Workers
    try:
        from celery import Celery
        app = Celery(broker='redis://localhost:6379/0')
        inspect = app.control.inspect()
        active = inspect.active()
        services["celery"] = {"status": "online" if active else "no_workers", "workers": len(active) if active else 0}
    except:
        services["celery"] = {"status": "unknown"}
    
    return {"ok": True, "services": services, "timestamp": datetime.now().isoformat()}
