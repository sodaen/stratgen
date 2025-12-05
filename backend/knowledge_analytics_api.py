"""
STRATGEN Knowledge Analytics API
Speichert und liefert historische Metriken für Dashboard-Visualisierung.
Ersetzt Grafana mit integrierter Lösung.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import threading
import time

router = APIRouter(prefix="/knowledge/analytics", tags=["Knowledge Analytics"])

# Metrics Storage
METRICS_DIR = Path("/home/sodaen/stratgen/data/metrics")
METRICS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = METRICS_DIR / "knowledge_history.json"
SEARCH_LOG_FILE = METRICS_DIR / "search_log.json"

_lock = threading.Lock()


class MetricsHistory:
    """Speichert historische Metriken mit Zeitstempel."""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self._load()
    
    def _load(self):
        """Lädt Historie aus Datei."""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {"snapshots": [], "searches": [], "ingestions": []}
        else:
            self.data = {"snapshots": [], "searches": [], "ingestions": []}
    
    def _save(self):
        """Speichert Historie in Datei."""
        with _lock:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.data, f)
    
    def add_snapshot(self, metrics: dict):
        """Fügt einen Metriken-Snapshot hinzu."""
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            **metrics
        }
        self.data["snapshots"].append(entry)
        
        # Limit
        if len(self.data["snapshots"]) > self.max_entries:
            self.data["snapshots"] = self.data["snapshots"][-self.max_entries:]
        
        self._save()
    
    def add_search(self, query: str, score: float, latency_ms: int, results_count: int):
        """Loggt eine Suchanfrage."""
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            "query": query[:100],
            "score": round(score, 3),
            "latency_ms": latency_ms,
            "results": results_count
        }
        self.data["searches"].append(entry)
        
        if len(self.data["searches"]) > self.max_entries:
            self.data["searches"] = self.data["searches"][-self.max_entries:]
        
        self._save()
    
    def add_ingestion(self, source: str, chunks: int, duration_ms: int, success: bool):
        """Loggt eine Ingestion."""
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            "source": source[:100],
            "chunks": chunks,
            "duration_ms": duration_ms,
            "success": success
        }
        self.data["ingestions"].append(entry)
        
        if len(self.data["ingestions"]) > self.max_entries:
            self.data["ingestions"] = self.data["ingestions"][-self.max_entries:]
        
        self._save()
    
    def get_snapshots(self, hours: int = 24) -> List[dict]:
        """Holt Snapshots der letzten X Stunden."""
        cutoff = int(time.time()) - (hours * 3600)
        return [s for s in self.data["snapshots"] if s.get("epoch", 0) > cutoff]
    
    def get_searches(self, hours: int = 24) -> List[dict]:
        """Holt Suchen der letzten X Stunden."""
        cutoff = int(time.time()) - (hours * 3600)
        return [s for s in self.data["searches"] if s.get("epoch", 0) > cutoff]
    
    def get_ingestions(self, hours: int = 24) -> List[dict]:
        """Holt Ingestions der letzten X Stunden."""
        cutoff = int(time.time()) - (hours * 3600)
        return [s for s in self.data["ingestions"] if s.get("epoch", 0) > cutoff]


# Singleton
history = MetricsHistory()


def collect_current_metrics() -> dict:
    """Sammelt aktuelle Knowledge-Metriken."""
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = {}
        total = 0
        
        for coll in client.get_collections().collections:
            info = client.get_collection(coll.name)
            collections[coll.name] = info.points_count
            total += info.points_count
        
        return {
            "total_chunks": total,
            "collections": collections,
            "knowledge_base": collections.get("knowledge_base", 0),
            "design_templates": collections.get("design_templates", 0),
            "external_sources": collections.get("external_sources", 0),
            "generated_outputs": collections.get("generated_outputs", 0)
        }
    except Exception as e:
        return {"error": str(e)}


# === API ENDPOINTS ===

@router.get("/current")
async def get_current_metrics():
    """Aktuelle Metriken abrufen und Snapshot speichern."""
    metrics = collect_current_metrics()
    
    # Snapshot speichern (max 1x pro Minute)
    snapshots = history.get_snapshots(hours=1)
    if not snapshots or (int(time.time()) - snapshots[-1].get("epoch", 0)) > 60:
        history.add_snapshot(metrics)
    
    return {"ok": True, **metrics}


@router.get("/history")
async def get_metrics_history(hours: int = 24):
    """Historische Metriken für Charts."""
    snapshots = history.get_snapshots(hours=hours)
    
    # Für Chart: Aggregiere auf Stunden-Basis
    hourly = {}
    for s in snapshots:
        hour_key = s["ts"][:13]  # YYYY-MM-DDTHH
        if hour_key not in hourly:
            hourly[hour_key] = s
    
    return {
        "ok": True,
        "hours": hours,
        "data_points": len(hourly),
        "snapshots": list(hourly.values())
    }


@router.get("/searches")
async def get_search_history(hours: int = 24):
    """Such-Historie für Analyse."""
    searches = history.get_searches(hours=hours)
    
    # Statistiken berechnen
    if searches:
        scores = [s["score"] for s in searches]
        latencies = [s["latency_ms"] for s in searches]
        
        stats = {
            "total": len(searches),
            "avg_score": round(sum(scores) / len(scores), 3),
            "min_score": round(min(scores), 3),
            "max_score": round(max(scores), 3),
            "avg_latency_ms": round(sum(latencies) / len(latencies)),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies))
        }
    else:
        stats = {"total": 0}
    
    # Gruppiere nach Stunde für Chart
    hourly_scores = {}
    hourly_counts = {}
    for s in searches:
        hour = s["ts"][:13]
        if hour not in hourly_scores:
            hourly_scores[hour] = []
            hourly_counts[hour] = 0
        hourly_scores[hour].append(s["score"])
        hourly_counts[hour] += 1
    
    chart_data = [
        {
            "hour": hour,
            "avg_score": round(sum(scores) / len(scores), 3),
            "count": hourly_counts[hour]
        }
        for hour, scores in sorted(hourly_scores.items())
    ]
    
    return {
        "ok": True,
        "hours": hours,
        "stats": stats,
        "recent": searches[-20:],  # Letzte 20
        "chart_data": chart_data
    }


@router.get("/ingestions")
async def get_ingestion_history(hours: int = 168):  # 7 Tage default
    """Ingestion-Historie."""
    ingestions = history.get_ingestions(hours=hours)
    
    # Statistiken
    if ingestions:
        total_chunks = sum(i["chunks"] for i in ingestions)
        successful = sum(1 for i in ingestions if i["success"])
        
        stats = {
            "total_ingestions": len(ingestions),
            "successful": successful,
            "failed": len(ingestions) - successful,
            "total_chunks_created": total_chunks,
            "avg_chunks_per_ingestion": round(total_chunks / len(ingestions), 1)
        }
    else:
        stats = {"total_ingestions": 0}
    
    # Gruppiere nach Tag
    daily = {}
    for i in ingestions:
        day = i["ts"][:10]
        if day not in daily:
            daily[day] = {"chunks": 0, "count": 0}
        daily[day]["chunks"] += i["chunks"]
        daily[day]["count"] += 1
    
    chart_data = [
        {"date": day, **data}
        for day, data in sorted(daily.items())
    ]
    
    return {
        "ok": True,
        "hours": hours,
        "stats": stats,
        "recent": ingestions[-20:],
        "chart_data": chart_data
    }


@router.get("/dashboard")
async def get_full_dashboard(hours: int = 24):
    """Komplettes Dashboard mit allen Daten."""
    current = collect_current_metrics()
    
    # Snapshot speichern
    history.add_snapshot(current)
    
    searches = history.get_searches(hours=hours)
    ingestions = history.get_ingestions(hours=hours * 7)  # 7x mehr für Ingestions
    
    # Search Stats
    if searches:
        scores = [s["score"] for s in searches]
        search_stats = {
            "total": len(searches),
            "avg_score": round(sum(scores) / len(scores), 3),
            "avg_latency": round(sum(s["latency_ms"] for s in searches) / len(searches))
        }
    else:
        search_stats = {"total": 0, "avg_score": 0, "avg_latency": 0}
    
    # Ingestion Stats
    if ingestions:
        ing_stats = {
            "total": len(ingestions),
            "chunks_created": sum(i["chunks"] for i in ingestions),
            "success_rate": round(sum(1 for i in ingestions if i["success"]) / len(ingestions) * 100)
        }
    else:
        ing_stats = {"total": 0, "chunks_created": 0, "success_rate": 0}
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "current": current,
        "search_stats": search_stats,
        "ingestion_stats": ing_stats,
        "recent_searches": searches[-10:],
        "recent_ingestions": ingestions[-10:]
    }


@router.post("/log/search")
async def log_search(query: str, score: float, latency_ms: int, results: int = 0):
    """Loggt eine Suchanfrage (wird von anderen Services aufgerufen)."""
    history.add_search(query, score, latency_ms, results)
    return {"ok": True}


@router.post("/log/ingestion")
async def log_ingestion(source: str, chunks: int, duration_ms: int, success: bool = True):
    """Loggt eine Ingestion."""
    history.add_ingestion(source, chunks, duration_ms, success)
    return {"ok": True}
