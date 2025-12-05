"""
STRATGEN Knowledge Analytics API - Vollständig
Ersetzt Grafana mit allen 6 Dashboard-Funktionen.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import json
import threading
import time
import statistics

router = APIRouter(prefix="/knowledge/analytics", tags=["Knowledge Analytics"])

METRICS_DIR = Path("/home/sodaen/stratgen/data/metrics")
METRICS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = METRICS_DIR / "knowledge_history.json"
_lock = threading.Lock()


class MetricsHistory:
    """Vollständige Metriken-Historie für alle Dashboards."""
    
    def __init__(self, max_entries: int = 50000):
        self.max_entries = max_entries
        self._load()
    
    def _load(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r') as f:
                    self.data = json.load(f)
            except:
                self._init_empty()
        else:
            self._init_empty()
    
    def _init_empty(self):
        self.data = {
            "snapshots": [],      # Periodische System-Snapshots
            "searches": [],       # Alle Suchanfragen
            "ingestions": [],     # Alle Ingestions
            "reranks": [],        # Re-Ranking Vergleiche
            "feedback": [],       # User Feedback
            "chunk_usage": {},    # Welche Chunks werden genutzt
            "quality_scores": {}, # Quality Scores per Source
        }
    
    def _save(self):
        with _lock:
            # Trim alte Einträge
            for key in ["snapshots", "searches", "ingestions", "reranks", "feedback"]:
                if len(self.data.get(key, [])) > self.max_entries:
                    self.data[key] = self.data[key][-self.max_entries:]
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
    
    # === SNAPSHOT METHODS ===
    def add_snapshot(self, metrics: dict):
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            **metrics
        }
        self.data["snapshots"].append(entry)
        self._save()
    
    def get_snapshots(self, hours: int = 24) -> List[dict]:
        cutoff = int(time.time()) - (hours * 3600)
        return [s for s in self.data["snapshots"] if s.get("epoch", 0) > cutoff]
    
    # === SEARCH METHODS ===
    def add_search(self, query: str, score: float, latency_ms: int, 
                   results_count: int, query_type: str = "general",
                   rerank_score: float = None):
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            "query": query[:200],
            "query_type": query_type,
            "score": round(score, 4),
            "rerank_score": round(rerank_score, 4) if rerank_score else None,
            "latency_ms": latency_ms,
            "results": results_count
        }
        self.data["searches"].append(entry)
        self._save()
    
    def get_searches(self, hours: int = 24) -> List[dict]:
        cutoff = int(time.time()) - (hours * 3600)
        return [s for s in self.data["searches"] if s.get("epoch", 0) > cutoff]
    
    # === INGESTION METHODS ===
    def add_ingestion(self, source: str, chunks_created: int, chunks_rejected: int,
                      rejection_reasons: dict, duration_ms: int, success: bool,
                      quality_scores: List[float] = None):
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            "source": source[:200],
            "chunks_created": chunks_created,
            "chunks_rejected": chunks_rejected,
            "rejection_reasons": rejection_reasons,
            "duration_ms": duration_ms,
            "success": success,
            "avg_quality": round(statistics.mean(quality_scores), 3) if quality_scores else None
        }
        self.data["ingestions"].append(entry)
        
        # Update quality scores per source
        if quality_scores:
            self.data["quality_scores"][source] = {
                "avg": round(statistics.mean(quality_scores), 3),
                "min": round(min(quality_scores), 3),
                "max": round(max(quality_scores), 3),
                "count": len(quality_scores),
                "updated": datetime.now().isoformat()
            }
        
        self._save()
    
    def get_ingestions(self, hours: int = 168) -> List[dict]:
        cutoff = int(time.time()) - (hours * 3600)
        return [i for i in self.data["ingestions"] if i.get("epoch", 0) > cutoff]
    
    # === CHUNK USAGE ===
    def record_chunk_usage(self, chunk_id: str, source: str):
        if chunk_id not in self.data["chunk_usage"]:
            self.data["chunk_usage"][chunk_id] = {
                "source": source,
                "count": 0,
                "last_used": None
            }
        self.data["chunk_usage"][chunk_id]["count"] += 1
        self.data["chunk_usage"][chunk_id]["last_used"] = datetime.now().isoformat()
        # Save periodically, not every time
        if len(self.data["chunk_usage"]) % 100 == 0:
            self._save()
    
    # === FEEDBACK ===
    def add_feedback(self, chunk_id: str, score: int, session_id: str = None):
        entry = {
            "ts": datetime.now().isoformat(),
            "epoch": int(time.time()),
            "chunk_id": chunk_id,
            "score": score,  # 1-5 or thumbs up/down
            "session_id": session_id
        }
        self.data["feedback"].append(entry)
        self._save()
    
    def get_feedback(self, hours: int = 168) -> List[dict]:
        cutoff = int(time.time()) - (hours * 3600)
        return [f for f in self.data["feedback"] if f.get("epoch", 0) > cutoff]


# Singleton
history = MetricsHistory()


def get_qdrant_stats() -> dict:
    """Holt aktuelle Qdrant Statistiken."""
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = {}
        total = 0
        
        for coll in client.get_collections().collections:
            info = client.get_collection(coll.name)
            collections[coll.name] = {
                "count": info.points_count,
                "status": info.status.value if hasattr(info.status, 'value') else str(info.status)
            }
            total += info.points_count
        
        return {
            "total_chunks": total,
            "collections": collections
        }
    except Exception as e:
        return {"error": str(e), "total_chunks": 0, "collections": {}}


def analyze_quality_distribution(client) -> dict:
    """Analysiert Quality Score Verteilung."""
    try:
        # Sample aus knowledge_base
        sample = client.scroll(
            collection_name="knowledge_base",
            limit=1000,
            with_payload=True,
            with_vectors=False
        )[0]
        
        scores = [p.payload.get("quality_score", 0.5) for p in sample if p.payload]
        
        if not scores:
            return {"buckets": [], "avg": 0, "median": 0}
        
        # Histogram Buckets
        buckets = {
            "0.0-0.5": 0, "0.5-0.6": 0, "0.6-0.7": 0,
            "0.7-0.8": 0, "0.8-0.9": 0, "0.9-1.0": 0
        }
        for s in scores:
            if s < 0.5: buckets["0.0-0.5"] += 1
            elif s < 0.6: buckets["0.5-0.6"] += 1
            elif s < 0.7: buckets["0.6-0.7"] += 1
            elif s < 0.8: buckets["0.7-0.8"] += 1
            elif s < 0.9: buckets["0.8-0.9"] += 1
            else: buckets["0.9-1.0"] += 1
        
        return {
            "buckets": [{"range": k, "count": v} for k, v in buckets.items()],
            "avg": round(statistics.mean(scores), 3),
            "median": round(statistics.median(scores), 3),
            "min": round(min(scores), 3),
            "max": round(max(scores), 3)
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# DASHBOARD 1: KNOWLEDGE OVERVIEW
# ============================================================

@router.get("/dashboard/overview")
async def dashboard_overview(hours: int = 24):
    """Dashboard 1: Knowledge Overview."""
    stats = get_qdrant_stats()
    snapshots = history.get_snapshots(hours=hours)
    
    # Trend berechnen
    if len(snapshots) >= 2:
        first_total = snapshots[0].get("total_chunks", 0)
        last_total = snapshots[-1].get("total_chunks", 0)
        trend = last_total - first_total
        trend_percent = round((trend / first_total * 100) if first_total else 0, 1)
    else:
        trend = 0
        trend_percent = 0
    
    # Quality Distribution
    from qdrant_client import QdrantClient
    client = QdrantClient(host="localhost", port=6333)
    quality_dist = analyze_quality_distribution(client)
    
    # Last Ingestion
    ingestions = history.get_ingestions(hours=168)
    last_ingestion = ingestions[-1] if ingestions else None
    
    # Collection Pie Data
    pie_data = [
        {"name": name, "value": info["count"]}
        for name, info in stats.get("collections", {}).items()
        if info["count"] > 0
    ]
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        
        # Gauge mit Trend
        "total_chunks": {
            "value": stats.get("total_chunks", 0),
            "trend": trend,
            "trend_percent": trend_percent
        },
        
        # Pie Chart
        "collections": pie_data,
        
        # Quality Histogram
        "quality_distribution": quality_dist,
        
        # Last Ingestion
        "last_ingestion": last_ingestion,
        
        # Trend Data für Line Chart
        "trend_data": [
            {
                "time": s["ts"][11:16],  # HH:MM
                "chunks": s.get("total_chunks", 0)
            }
            for s in snapshots[-48:]  # Letzte 48 Datenpunkte
        ]
    }


# ============================================================
# DASHBOARD 2: SEARCH PERFORMANCE
# ============================================================

@router.get("/dashboard/search")
async def dashboard_search(hours: int = 24):
    """Dashboard 2: Search Performance."""
    searches = history.get_searches(hours=hours)
    
    if not searches:
        return {
            "ok": True,
            "total_searches": 0,
            "score_trend": [],
            "score_distribution": [],
            "latency_percentiles": {},
            "searches_per_hour": []
        }
    
    # Score Trend (pro Stunde)
    hourly_scores = defaultdict(list)
    hourly_counts = defaultdict(int)
    for s in searches:
        hour = s["ts"][:13]  # YYYY-MM-DDTHH
        hourly_scores[hour].append(s["score"])
        hourly_counts[hour] += 1
    
    score_trend = [
        {
            "hour": hour[-5:],  # HH:00
            "avg_score": round(statistics.mean(scores), 3),
            "count": hourly_counts[hour]
        }
        for hour, scores in sorted(hourly_scores.items())
    ]
    
    # Score Distribution (Histogram)
    all_scores = [s["score"] for s in searches]
    score_buckets = {"<0.5": 0, "0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0, ">0.9": 0}
    for score in all_scores:
        if score < 0.5: score_buckets["<0.5"] += 1
        elif score < 0.6: score_buckets["0.5-0.6"] += 1
        elif score < 0.7: score_buckets["0.6-0.7"] += 1
        elif score < 0.8: score_buckets["0.7-0.8"] += 1
        elif score < 0.9: score_buckets["0.8-0.9"] += 1
        else: score_buckets[">0.9"] += 1
    
    score_distribution = [{"range": k, "count": v} for k, v in score_buckets.items()]
    
    # Latency Percentiles
    latencies = sorted([s["latency_ms"] for s in searches])
    n = len(latencies)
    latency_percentiles = {
        "p50": latencies[int(n * 0.5)] if n > 0 else 0,
        "p90": latencies[int(n * 0.9)] if n > 0 else 0,
        "p95": latencies[int(n * 0.95)] if n > 0 else 0,
        "p99": latencies[int(n * 0.99)] if n > 0 else 0,
        "avg": round(statistics.mean(latencies)) if latencies else 0
    }
    
    # Searches per Hour (Bar Chart)
    searches_per_hour = [
        {"hour": hour[-5:], "count": hourly_counts[hour]}
        for hour in sorted(hourly_counts.keys())
    ]
    
    return {
        "ok": True,
        "total_searches": len(searches),
        "avg_score": round(statistics.mean(all_scores), 3),
        "score_trend": score_trend,
        "score_distribution": score_distribution,
        "latency_percentiles": latency_percentiles,
        "searches_per_hour": searches_per_hour,
        "recent": searches[-20:]
    }


# ============================================================
# DASHBOARD 3: SCORE OPTIMIZATION
# ============================================================

@router.get("/dashboard/optimization")
async def dashboard_optimization(hours: int = 24):
    """Dashboard 3: Score-Optimierung."""
    searches = history.get_searches(hours=hours)
    
    # Nur Suchen mit Re-Ranking
    reranked = [s for s in searches if s.get("rerank_score") is not None]
    
    # Score vor/nach Re-Ranking
    if reranked:
        before_scores = [s["score"] for s in reranked]
        after_scores = [s["rerank_score"] for s in reranked]
        
        rerank_comparison = {
            "before_avg": round(statistics.mean(before_scores), 3),
            "after_avg": round(statistics.mean(after_scores), 3),
            "improvement": round(statistics.mean(after_scores) - statistics.mean(before_scores), 3),
            "improvement_percent": round((statistics.mean(after_scores) - statistics.mean(before_scores)) / statistics.mean(before_scores) * 100, 1) if before_scores else 0,
            "samples": len(reranked)
        }
    else:
        rerank_comparison = {"before_avg": 0, "after_avg": 0, "improvement": 0, "samples": 0}
    
    # Score by Query Type
    by_type = defaultdict(list)
    for s in searches:
        by_type[s.get("query_type", "general")].append(s["score"])
    
    score_by_type = [
        {
            "type": qtype,
            "avg_score": round(statistics.mean(scores), 3),
            "count": len(scores)
        }
        for qtype, scores in sorted(by_type.items())
    ]
    
    # Score Improvement Trend (täglich)
    daily_scores = defaultdict(list)
    for s in searches:
        day = s["ts"][:10]
        daily_scores[day].append(s["score"])
    
    improvement_trend = [
        {
            "date": day,
            "avg_score": round(statistics.mean(scores), 3)
        }
        for day, scores in sorted(daily_scores.items())
    ]
    
    return {
        "ok": True,
        "rerank_comparison": rerank_comparison,
        "score_by_type": score_by_type,
        "improvement_trend": improvement_trend,
        "total_searches": len(searches),
        "reranked_searches": len(reranked)
    }


# ============================================================
# DASHBOARD 4: INGESTION MONITOR
# ============================================================

@router.get("/dashboard/ingestion")
async def dashboard_ingestion(hours: int = 168):
    """Dashboard 4: Ingestion Monitor."""
    ingestions = history.get_ingestions(hours=hours)
    
    if not ingestions:
        return {
            "ok": True,
            "total_files": 0,
            "chunks_created": 0,
            "chunks_rejected": 0,
            "rejection_reasons": [],
            "daily_ingestions": []
        }
    
    # Totals
    total_created = sum(i["chunks_created"] for i in ingestions)
    total_rejected = sum(i["chunks_rejected"] for i in ingestions)
    
    # Rejection Reasons (Pie Chart)
    all_reasons = Counter()
    for i in ingestions:
        for reason, count in i.get("rejection_reasons", {}).items():
            all_reasons[reason] += count
    
    rejection_reasons = [
        {"reason": reason, "count": count}
        for reason, count in all_reasons.most_common()
    ]
    
    # Daily Ingestions (Stacked Bar)
    daily = defaultdict(lambda: {"created": 0, "rejected": 0, "count": 0, "duration": 0})
    for i in ingestions:
        day = i["ts"][:10]
        daily[day]["created"] += i["chunks_created"]
        daily[day]["rejected"] += i["chunks_rejected"]
        daily[day]["count"] += 1
        daily[day]["duration"] += i["duration_ms"]
    
    daily_ingestions = [
        {
            "date": day,
            "created": data["created"],
            "rejected": data["rejected"],
            "files": data["count"],
            "avg_duration_ms": round(data["duration"] / data["count"]) if data["count"] else 0
        }
        for day, data in sorted(daily.items())
    ]
    
    # Duration Trend
    duration_trend = [
        {
            "time": i["ts"][11:16],
            "duration_ms": i["duration_ms"]
        }
        for i in ingestions[-50:]
    ]
    
    return {
        "ok": True,
        "total_files": len(ingestions),
        "chunks_created": total_created,
        "chunks_rejected": total_rejected,
        "success_rate": round(sum(1 for i in ingestions if i["success"]) / len(ingestions) * 100, 1),
        "rejection_reasons": rejection_reasons,
        "daily_ingestions": daily_ingestions,
        "duration_trend": duration_trend,
        "recent": ingestions[-10:]
    }


# ============================================================
# DASHBOARD 5: MATERIAL QUALITY
# ============================================================

@router.get("/dashboard/quality")
async def dashboard_quality():
    """Dashboard 5: Material Quality."""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    # Sample für Analyse
    try:
        sample = client.scroll(
            collection_name="knowledge_base",
            limit=2000,
            with_payload=True,
            with_vectors=False
        )[0]
    except:
        sample = []
    
    # Quality Score by Source
    source_scores = defaultdict(list)
    source_dates = {}
    for p in sample:
        if not p.payload:
            continue
        source = p.payload.get("source_file", "unknown")
        score = p.payload.get("quality_score", 0.5)
        source_scores[source].append(score)
        
        indexed_at = p.payload.get("indexed_at", "")
        if indexed_at and (source not in source_dates or indexed_at > source_dates[source]):
            source_dates[source] = indexed_at
    
    quality_by_source = sorted([
        {
            "source": source,
            "avg_score": round(statistics.mean(scores), 3),
            "chunks": len(scores),
            "min_score": round(min(scores), 3),
            "max_score": round(max(scores), 3)
        }
        for source, scores in source_scores.items()
    ], key=lambda x: x["avg_score"], reverse=True)
    
    # Content Freshness
    now = datetime.now()
    freshness_buckets = {"<1 day": 0, "1-7 days": 0, "7-30 days": 0, ">30 days": 0, "unknown": 0}
    for source, date_str in source_dates.items():
        if not date_str:
            freshness_buckets["unknown"] += 1
            continue
        try:
            indexed = datetime.fromisoformat(date_str.replace("Z", "+00:00").replace("+00:00", ""))
            age = (now - indexed).days
            if age < 1: freshness_buckets["<1 day"] += 1
            elif age < 7: freshness_buckets["1-7 days"] += 1
            elif age < 30: freshness_buckets["7-30 days"] += 1
            else: freshness_buckets[">30 days"] += 1
        except:
            freshness_buckets["unknown"] += 1
    
    # Most Used Chunks
    chunk_usage = history.data.get("chunk_usage", {})
    most_used = sorted(
        [{"id": k, **v} for k, v in chunk_usage.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]
    
    # Unused Chunks (nie benutzt)
    all_chunk_ids = set(str(p.id) for p in sample)
    used_ids = set(chunk_usage.keys())
    unused_count = len(all_chunk_ids - used_ids)
    
    return {
        "ok": True,
        "quality_by_source": quality_by_source[:30],  # Top 30
        "freshness": [{"period": k, "count": v} for k, v in freshness_buckets.items()],
        "most_used_chunks": most_used,
        "unused_chunks": {
            "count": unused_count,
            "percent": round(unused_count / len(all_chunk_ids) * 100, 1) if all_chunk_ids else 0
        },
        "total_sources": len(source_scores),
        "avg_quality_overall": round(
            statistics.mean([s for scores in source_scores.values() for s in scores]), 3
        ) if source_scores else 0
    }


# ============================================================
# DASHBOARD 6: SELF-LEARNING
# ============================================================

@router.get("/dashboard/learning")
async def dashboard_learning(hours: int = 168):
    """Dashboard 6: Self-Learning."""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    # Generated Outputs Collection
    try:
        gen_info = client.get_collection("generated_outputs")
        generated_count = gen_info.points_count
    except:
        generated_count = 0
    
    # Feedback Scores
    feedback = history.get_feedback(hours=hours)
    
    if feedback:
        scores = [f["score"] for f in feedback]
        feedback_stats = {
            "total": len(feedback),
            "avg_score": round(statistics.mean(scores), 2),
            "positive": sum(1 for s in scores if s >= 4),
            "negative": sum(1 for s in scores if s <= 2),
            "neutral": sum(1 for s in scores if 2 < s < 4)
        }
        
        # Distribution
        score_dist = Counter(scores)
        feedback_distribution = [
            {"score": k, "count": v}
            for k, v in sorted(score_dist.items())
        ]
    else:
        feedback_stats = {"total": 0, "avg_score": 0, "positive": 0, "negative": 0, "neutral": 0}
        feedback_distribution = []
    
    # Learning Trend (täglich)
    daily_feedback = defaultdict(list)
    for f in feedback:
        day = f["ts"][:10]
        daily_feedback[day].append(f["score"])
    
    learning_trend = [
        {
            "date": day,
            "avg_score": round(statistics.mean(scores), 2),
            "count": len(scores)
        }
        for day, scores in sorted(daily_feedback.items())
    ]
    
    # Best Performing Templates (from design_templates)
    try:
        templates = client.scroll(
            collection_name="design_templates",
            limit=200,
            with_payload=True,
            with_vectors=False
        )[0]
        
        template_scores = defaultdict(list)
        for t in templates:
            if t.payload:
                source = t.payload.get("source_file", "unknown")
                score = t.payload.get("quality_score", 0.5)
                template_scores[source].append(score)
        
        best_templates = sorted([
            {
                "template": source,
                "avg_score": round(statistics.mean(scores), 3),
                "chunks": len(scores)
            }
            for source, scores in template_scores.items()
        ], key=lambda x: x["avg_score"], reverse=True)[:10]
    except:
        best_templates = []
    
    return {
        "ok": True,
        "generated_outputs": {
            "total": generated_count,
            "indexed_for_learning": generated_count
        },
        "feedback_stats": feedback_stats,
        "feedback_distribution": feedback_distribution,
        "learning_trend": learning_trend,
        "best_templates": best_templates
    }


# ============================================================
# LOGGING ENDPOINTS (für andere Services)
# ============================================================

@router.post("/log/search")
async def log_search(
    query: str,
    score: float,
    latency_ms: int,
    results: int = 0,
    query_type: str = "general",
    rerank_score: float = None
):
    """Loggt eine Suchanfrage."""
    history.add_search(query, score, latency_ms, results, query_type, rerank_score)
    return {"ok": True}


@router.post("/log/ingestion")
async def log_ingestion(
    source: str,
    chunks_created: int,
    chunks_rejected: int = 0,
    rejection_reasons: dict = None,
    duration_ms: int = 0,
    success: bool = True,
    quality_scores: List[float] = None
):
    """Loggt eine Ingestion."""
    history.add_ingestion(
        source, chunks_created, chunks_rejected,
        rejection_reasons or {}, duration_ms, success, quality_scores
    )
    return {"ok": True}


@router.post("/log/feedback")
async def log_feedback(chunk_id: str, score: int, session_id: str = None):
    """Loggt User Feedback."""
    history.add_feedback(chunk_id, score, session_id)
    return {"ok": True}


@router.post("/log/chunk_usage")
async def log_chunk_usage(chunk_id: str, source: str):
    """Loggt Chunk-Nutzung."""
    history.record_chunk_usage(chunk_id, source)
    return {"ok": True}


# ============================================================
# COMBINED DASHBOARD (Übersicht)
# ============================================================

@router.get("/dashboard/all")
async def dashboard_all(hours: int = 24):
    """Kombiniertes Dashboard mit allen Metriken."""
    overview = await dashboard_overview(hours)
    search = await dashboard_search(hours)
    optimization = await dashboard_optimization(hours)
    ingestion = await dashboard_ingestion(hours * 7)
    quality = await dashboard_quality()
    learning = await dashboard_learning(hours * 7)
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "overview": overview,
        "search": search,
        "optimization": optimization,
        "ingestion": ingestion,
        "quality": quality,
        "learning": learning
    }


@router.get("/current")
async def get_current():
    """Schneller aktueller Status."""
    stats = get_qdrant_stats()
    history.add_snapshot(stats)
    return {"ok": True, **stats}
