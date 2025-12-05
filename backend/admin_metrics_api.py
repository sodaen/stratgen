"""
Admin Metrics API für Stratgen.
Umfassende System-Metriken, Quality Scores und Analytics.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import psutil
import json
import time
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict

router = APIRouter(prefix="/admin", tags=["admin"])

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
METRICS_DIR = DATA_ROOT / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# === HELPER FUNCTIONS ===

def _get_db_connection():
    """SQLite connection for metrics storage."""
    db_path = METRICS_DIR / "admin_metrics.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _init_metrics_db():
    """Initialize metrics database."""
    conn = _get_db_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS system_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL,
            memory_percent REAL,
            memory_used_gb REAL,
            disk_percent REAL,
            disk_used_gb REAL,
            api_response_ms REAL,
            ollama_ok INTEGER,
            qdrant_ok INTEGER,
            redis_ok INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS generation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            event_type TEXT,
            slides_count INTEGER,
            duration_ms INTEGER,
            quality_score REAL,
            briefing_score REAL,
            critique_score REAL,
            iteration INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS search_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            query TEXT,
            results_count INTEGER,
            top_score REAL,
            avg_score REAL,
            latency_ms INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS error_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_type TEXT,
            message TEXT,
            endpoint TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_system_ts ON system_snapshots(timestamp);
        CREATE INDEX IF NOT EXISTS idx_gen_ts ON generation_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_search_ts ON search_events(timestamp);
    """)
    conn.commit()
    conn.close()

_init_metrics_db()


def _record_system_snapshot():
    """Record current system state."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check services
        import httpx
        
        api_start = time.time()
        try:
            httpx.get("http://localhost:8011/health", timeout=2)
            api_ms = (time.time() - api_start) * 1000
        except:
            api_ms = -1
        
        ollama_ok = 0
        try:
            r = httpx.get("http://localhost:11434/api/tags", timeout=2)
            ollama_ok = 1 if r.status_code == 200 else 0
        except:
            pass
        
        qdrant_ok = 0
        try:
            r = httpx.get("http://localhost:6333/collections", timeout=2)
            qdrant_ok = 1 if r.status_code == 200 else 0
        except:
            pass
        
        redis_ok = 0
        try:
            import redis
            r = redis.Redis()
            r.ping()
            redis_ok = 1
        except:
            pass
        
        conn = _get_db_connection()
        conn.execute("""
            INSERT INTO system_snapshots 
            (cpu_percent, memory_percent, memory_used_gb, disk_percent, disk_used_gb,
             api_response_ms, ollama_ok, qdrant_ok, redis_ok)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cpu, mem.percent, mem.used / (1024**3), disk.percent, disk.used / (1024**3),
              api_ms, ollama_ok, qdrant_ok, redis_ok))
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Snapshot error: {e}")


# === SYSTEM METRICS ===

@router.get("/metrics/system")
async def get_system_metrics():
    """Aktuelle System-Metriken."""
    _record_system_snapshot()
    
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process info
    process = psutil.Process()
    
    # Load averages
    load = psutil.getloadavg()
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "percent": cpu,
            "cores": psutil.cpu_count(),
            "load_1m": load[0],
            "load_5m": load[1],
            "load_15m": load[2]
        },
        "memory": {
            "percent": mem.percent,
            "used_gb": round(mem.used / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2)
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2)
        },
        "process": {
            "memory_mb": round(process.memory_info().rss / (1024**2), 1),
            "threads": process.num_threads(),
            "cpu_percent": process.cpu_percent()
        }
    }


@router.get("/metrics/system/history")
async def get_system_history(hours: int = 24):
    """System-Metriken der letzten X Stunden."""
    conn = _get_db_connection()
    cutoff = datetime.now() - timedelta(hours=hours)
    
    rows = conn.execute("""
        SELECT timestamp, cpu_percent, memory_percent, disk_percent, 
               api_response_ms, ollama_ok, qdrant_ok, redis_ok
        FROM system_snapshots
        WHERE timestamp > ?
        ORDER BY timestamp ASC
    """, (cutoff.isoformat(),)).fetchall()
    conn.close()
    
    return {
        "ok": True,
        "hours": hours,
        "count": len(rows),
        "data": [
            {
                "timestamp": r["timestamp"],
                "cpu": r["cpu_percent"],
                "memory": r["memory_percent"],
                "disk": r["disk_percent"],
                "api_ms": r["api_response_ms"],
                "services": {
                    "ollama": bool(r["ollama_ok"]),
                    "qdrant": bool(r["qdrant_ok"]),
                    "redis": bool(r["redis_ok"])
                }
            }
            for r in rows
        ]
    }


@router.get("/metrics/services")
async def get_services_status():
    """Detaillierter Service-Status."""
    import httpx
    
    services = {}
    
    # API
    try:
        start = time.time()
        r = httpx.get("http://localhost:8011/health", timeout=5)
        services["api"] = {
            "status": "online",
            "response_ms": round((time.time() - start) * 1000, 1),
            "data": r.json()
        }
    except Exception as e:
        services["api"] = {"status": "offline", "error": str(e)}
    
    # Ollama
    try:
        start = time.time()
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        models = r.json().get("models", [])
        services["ollama"] = {
            "status": "online",
            "response_ms": round((time.time() - start) * 1000, 1),
            "models": [m["name"] for m in models],
            "model_count": len(models)
        }
    except Exception as e:
        services["ollama"] = {"status": "offline", "error": str(e)}
    
    # Qdrant
    try:
        start = time.time()
        r = httpx.get("http://localhost:6333/collections", timeout=5)
        collections = r.json().get("result", {}).get("collections", [])
        
        collection_details = {}
        for coll in collections:
            try:
                cr = httpx.get(f"http://localhost:6333/collections/{coll['name']}", timeout=2)
                info = cr.json().get("result", {})
                collection_details[coll["name"]] = {
                    "points": info.get("points_count", 0),
                    "status": info.get("status", "unknown")
                }
            except:
                pass
        
        services["qdrant"] = {
            "status": "online",
            "response_ms": round((time.time() - start) * 1000, 1),
            "collections": collection_details,
            "total_points": sum(c.get("points", 0) for c in collection_details.values())
        }
    except Exception as e:
        services["qdrant"] = {"status": "offline", "error": str(e)}
    
    # Redis
    try:
        import redis
        start = time.time()
        r = redis.Redis()
        r.ping()
        info = r.info()
        services["redis"] = {
            "status": "online",
            "response_ms": round((time.time() - start) * 1000, 1),
            "used_memory_mb": round(info.get("used_memory", 0) / (1024**2), 1),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 1)
        }
    except Exception as e:
        services["redis"] = {"status": "offline", "error": str(e)}
    
    # Celery
    try:
        from celery import Celery
        app = Celery(broker='redis://localhost:6379/0')
        inspect = app.control.inspect(timeout=2)
        active = inspect.active() or {}
        stats = inspect.stats() or {}
        
        services["celery"] = {
            "status": "online" if active else "no_workers",
            "workers": len(active),
            "worker_names": list(active.keys()),
            "tasks_active": sum(len(t) for t in active.values())
        }
    except Exception as e:
        services["celery"] = {"status": "offline", "error": str(e)}
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


# === KNOWLEDGE METRICS ===

@router.get("/metrics/knowledge")
async def get_knowledge_metrics():
    """RAG & Knowledge Base Metriken."""
    stats = {
        "corpus": {},
        "retrieval": {},
        "coverage": {}
    }
    
    # Qdrant stats
    try:
        import httpx
        r = httpx.get("http://localhost:6333/collections", timeout=5)
        collections = r.json().get("result", {}).get("collections", [])
        
        total_points = 0
        collection_stats = {}
        
        for coll in collections:
            try:
                cr = httpx.get(f"http://localhost:6333/collections/{coll['name']}", timeout=2)
                info = cr.json().get("result", {})
                points = info.get("points_count", 0)
                total_points += points
                collection_stats[coll["name"]] = {
                    "points": points,
                    "status": info.get("status", "unknown"),
                    "vectors_size": info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 384)
                }
            except:
                pass
        
        stats["corpus"] = {
            "total_chunks": total_points,
            "collections": collection_stats,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dim": 384
        }
    except Exception as e:
        stats["corpus"]["error"] = str(e)
    
    # Knowledge files
    knowledge_dir = DATA_ROOT / "knowledge"
    if knowledge_dir.exists():
        files_by_type = Counter()
        total_size = 0
        
        for f in knowledge_dir.rglob("*"):
            if f.is_file():
                files_by_type[f.suffix.lower()] += 1
                total_size += f.stat().st_size
        
        stats["corpus"]["files"] = {
            "total": sum(files_by_type.values()),
            "by_type": dict(files_by_type),
            "total_size_mb": round(total_size / (1024**2), 2)
        }
    
    # Search quality (from recent searches)
    conn = _get_db_connection()
    recent_searches = conn.execute("""
        SELECT AVG(top_score) as avg_top, AVG(avg_score) as avg_all,
               AVG(latency_ms) as avg_latency, COUNT(*) as count,
               SUM(CASE WHEN top_score > 0.6 THEN 1 ELSE 0 END) as good_hits
        FROM search_events
        WHERE timestamp > datetime('now', '-24 hours')
    """).fetchone()
    conn.close()
    
    if recent_searches and recent_searches["count"] > 0:
        stats["retrieval"] = {
            "searches_24h": recent_searches["count"],
            "avg_top_score": round(recent_searches["avg_top"] or 0, 3),
            "avg_score": round(recent_searches["avg_all"] or 0, 3),
            "avg_latency_ms": round(recent_searches["avg_latency"] or 0, 1),
            "hit_rate": round((recent_searches["good_hits"] or 0) / recent_searches["count"] * 100, 1)
        }
    
    return {"ok": True, "timestamp": datetime.now().isoformat(), **stats}


@router.post("/metrics/search/log")
async def log_search_event(data: dict):
    """Log a search event for analytics."""
    conn = _get_db_connection()
    conn.execute("""
        INSERT INTO search_events (query, results_count, top_score, avg_score, latency_ms)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("query", "")[:200],
        data.get("results_count", 0),
        data.get("top_score", 0),
        data.get("avg_score", 0),
        data.get("latency_ms", 0)
    ))
    conn.commit()
    conn.close()
    return {"ok": True}


# === GENERATION METRICS ===

@router.get("/metrics/generation")
async def get_generation_metrics():
    """Generation & Quality Metriken."""
    stats = {
        "output": {},
        "quality": {},
        "performance": {}
    }
    
    # Sessions & Exports
    sessions_dir = DATA_ROOT / "sessions"
    exports_dir = DATA_ROOT / "exports"
    
    total_sessions = 0
    total_slides = 0
    session_details = []
    
    if sessions_dir.exists():
        for sd in sessions_dir.iterdir():
            if sd.is_dir():
                total_sessions += 1
                
                slides_file = sd / "slides.json"
                meta_file = sd / "meta.json"
                
                slides_count = 0
                if slides_file.exists():
                    try:
                        slides = json.loads(slides_file.read_text())
                        slides_count = len(slides) if isinstance(slides, list) else 0
                        total_slides += slides_count
                    except:
                        pass
                
                created = None
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text())
                        created = meta.get("created_at")
                    except:
                        pass
                
                session_details.append({
                    "id": sd.name,
                    "slides": slides_count,
                    "created": created
                })
    
    exports_count = len(list(exports_dir.glob("*.pptx"))) if exports_dir.exists() else 0
    
    stats["output"] = {
        "total_sessions": total_sessions,
        "total_slides": total_slides,
        "avg_slides_per_session": round(total_slides / max(total_sessions, 1), 1),
        "exports": exports_count,
        "recent_sessions": sorted(session_details, key=lambda x: x.get("created") or "", reverse=True)[:10]
    }
    
    # Generation events from DB
    conn = _get_db_connection()
    
    gen_stats = conn.execute("""
        SELECT 
            COUNT(*) as count,
            AVG(slides_count) as avg_slides,
            AVG(duration_ms) as avg_duration,
            AVG(quality_score) as avg_quality,
            AVG(briefing_score) as avg_briefing,
            AVG(critique_score) as avg_critique
        FROM generation_events
        WHERE timestamp > datetime('now', '-7 days')
    """).fetchone()
    
    if gen_stats and gen_stats["count"] > 0:
        stats["quality"] = {
            "generations_7d": gen_stats["count"],
            "avg_quality_score": round(gen_stats["avg_quality"] or 0, 2),
            "avg_briefing_score": round(gen_stats["avg_briefing"] or 0, 2),
            "avg_critique_score": round(gen_stats["avg_critique"] or 0, 2)
        }
        stats["performance"] = {
            "avg_duration_ms": round(gen_stats["avg_duration"] or 0, 0),
            "avg_slides": round(gen_stats["avg_slides"] or 0, 1)
        }
    
    # Hourly generation counts for chart
    hourly = conn.execute("""
        SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour, COUNT(*) as count
        FROM generation_events
        WHERE timestamp > datetime('now', '-48 hours')
        GROUP BY hour
        ORDER BY hour
    """).fetchall()
    
    stats["hourly_generations"] = [{"hour": r["hour"], "count": r["count"]} for r in hourly]
    
    conn.close()
    
    return {"ok": True, "timestamp": datetime.now().isoformat(), **stats}


@router.post("/metrics/generation/log")
async def log_generation_event(data: dict):
    """Log a generation event."""
    conn = _get_db_connection()
    conn.execute("""
        INSERT INTO generation_events 
        (session_id, event_type, slides_count, duration_ms, quality_score, briefing_score, critique_score, iteration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("session_id", ""),
        data.get("event_type", "generation"),
        data.get("slides_count", 0),
        data.get("duration_ms", 0),
        data.get("quality_score"),
        data.get("briefing_score"),
        data.get("critique_score"),
        data.get("iteration", 1)
    ))
    conn.commit()
    conn.close()
    return {"ok": True}


# === LEARNING METRICS ===

@router.get("/metrics/learning")
async def get_learning_metrics():
    """Learning & Feedback Metriken."""
    stats = {
        "templates": {},
        "feedback": {},
        "growth": {}
    }
    
    # Template learning
    template_cache = DATA_ROOT / "knowledge" / "templates_learned.json"
    if template_cache.exists():
        try:
            cache = json.loads(template_cache.read_text())
            stats["templates"] = {
                "learned": len(cache.get("templates", {})),
                "patterns": cache.get("patterns", {}),
                "last_scan": cache.get("last_scan")
            }
        except:
            pass
    
    # Chat feedback
    feedback_dir = DATA_ROOT / "knowledge" / "chat_feedback"
    if feedback_dir.exists():
        feedback_files = list(feedback_dir.glob("feedback_*.json"))
        positive = negative = neutral = 0
        
        for f in feedback_files:
            try:
                fb = json.loads(f.read_text())
                rating = fb.get("rating", "neutral")
                if rating == "positive":
                    positive += 1
                elif rating == "negative":
                    negative += 1
                else:
                    neutral += 1
            except:
                pass
        
        stats["feedback"] = {
            "total": len(feedback_files),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "satisfaction_rate": round(positive / max(len(feedback_files), 1) * 100, 1)
        }
    
    # Knowledge growth (files added over time)
    knowledge_dir = DATA_ROOT / "knowledge"
    if knowledge_dir.exists():
        files_by_date = defaultdict(int)
        for f in knowledge_dir.rglob("*"):
            if f.is_file():
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    date_key = mtime.strftime("%Y-%m-%d")
                    files_by_date[date_key] += 1
                except:
                    pass
        
        sorted_dates = sorted(files_by_date.items())[-30:]  # Last 30 days
        stats["growth"] = {
            "files_by_date": [{"date": d, "count": c} for d, c in sorted_dates],
            "total_files": sum(files_by_date.values())
        }
    
    return {"ok": True, "timestamp": datetime.now().isoformat(), **stats}


# === AGGREGATED DASHBOARD ===

@router.get("/metrics/dashboard")
async def get_dashboard_metrics():
    """Alle wichtigen Metriken für das Dashboard."""
    system = await get_system_metrics()
    services = await get_services_status()
    knowledge = await get_knowledge_metrics()
    generation = await get_generation_metrics()
    learning = await get_learning_metrics()
    history = await get_system_history(hours=24)
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "system": system,
        "services": services.get("services", {}),
        "knowledge": knowledge,
        "generation": generation,
        "learning": learning,
        "history": history.get("data", [])
    }


# === ERROR TRACKING ===

@router.post("/metrics/error")
async def log_error(data: dict):
    """Log an error event."""
    conn = _get_db_connection()
    conn.execute("""
        INSERT INTO error_events (error_type, message, endpoint)
        VALUES (?, ?, ?)
    """, (
        data.get("error_type", "unknown"),
        data.get("message", "")[:500],
        data.get("endpoint", "")
    ))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/metrics/errors")
async def get_errors(hours: int = 24):
    """Error events der letzten X Stunden."""
    conn = _get_db_connection()
    cutoff = datetime.now() - timedelta(hours=hours)
    
    rows = conn.execute("""
        SELECT timestamp, error_type, message, endpoint
        FROM error_events
        WHERE timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (cutoff.isoformat(),)).fetchall()
    
    by_type = conn.execute("""
        SELECT error_type, COUNT(*) as count
        FROM error_events
        WHERE timestamp > ?
        GROUP BY error_type
        ORDER BY count DESC
    """, (cutoff.isoformat(),)).fetchall()
    
    conn.close()
    
    return {
        "ok": True,
        "hours": hours,
        "total": len(rows),
        "by_type": {r["error_type"]: r["count"] for r in by_type},
        "recent": [dict(r) for r in rows[:20]]
    }
