"""
STRATGEN Knowledge Metrics
Prometheus Exporter für Knowledge System

Speichere als: /home/sodaen/stratgen/services/knowledge_metrics.py
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from threading import Lock
import json

logger = logging.getLogger(__name__)

# Metrics Storage (in-memory + File-Persist)
METRICS_FILE = Path("/home/sodaen/stratgen/data/metrics/knowledge_metrics.json")
METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)


class KnowledgeMetrics:
    """
    Sammelt und exportiert Knowledge-Metriken.
    """
    
    def __init__(self):
        self._lock = Lock()
        self._metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        """Lädt persistierte Metriken."""
        if METRICS_FILE.exists():
            try:
                return json.loads(METRICS_FILE.read_text())
            except:
                pass
        
        return {
            "chunks": {},           # collection -> count
            "ingestion": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "duration_sum": 0.0,
                "by_source_type": {}
            },
            "quality": {
                "scores_sum": 0.0,
                "scores_count": 0,
                "rejected_duplicate": 0,
                "rejected_spam": 0,
                "rejected_length": 0
            },
            "usage": {
                "searches_total": 0,
                "latency_sum": 0.0,
                "latency_count": 0,
                "hits_high": 0,      # score > 0.7
                "hits_medium": 0,    # 0.4 < score <= 0.7
                "hits_low": 0        # score <= 0.4
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_metrics(self):
        """Speichert Metriken."""
        self._metrics["last_updated"] = datetime.now().isoformat()
        try:
            METRICS_FILE.write_text(json.dumps(self._metrics, indent=2))
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    # === INGESTION METRICS ===
    
    def record_ingestion(self, 
                         source_type: str,
                         success: bool,
                         chunks_created: int,
                         duration_ms: float,
                         quality_score: float = None):
        """Zeichnet Ingestion-Event auf."""
        with self._lock:
            self._metrics["ingestion"]["total"] += 1
            self._metrics["ingestion"]["duration_sum"] += duration_ms
            
            if success:
                self._metrics["ingestion"]["success"] += 1
            else:
                self._metrics["ingestion"]["failed"] += 1
            
            # By source type
            if source_type not in self._metrics["ingestion"]["by_source_type"]:
                self._metrics["ingestion"]["by_source_type"][source_type] = {"count": 0, "chunks": 0}
            self._metrics["ingestion"]["by_source_type"][source_type]["count"] += 1
            self._metrics["ingestion"]["by_source_type"][source_type]["chunks"] += chunks_created
            
            # Quality
            if quality_score is not None:
                self._metrics["quality"]["scores_sum"] += quality_score
                self._metrics["quality"]["scores_count"] += 1
            
            self._save_metrics()
    
    def record_rejection(self, reason: str):
        """Zeichnet Ablehnung auf."""
        with self._lock:
            key = f"rejected_{reason}"
            if key in self._metrics["quality"]:
                self._metrics["quality"][key] += 1
            self._save_metrics()
    
    def update_chunk_count(self, collection: str, count: int):
        """Aktualisiert Chunk-Anzahl für Collection."""
        with self._lock:
            self._metrics["chunks"][collection] = count
            self._save_metrics()
    
    # === USAGE METRICS ===
    
    def record_search(self, latency_ms: float, top_score: float = None):
        """Zeichnet Such-Event auf."""
        with self._lock:
            self._metrics["usage"]["searches_total"] += 1
            self._metrics["usage"]["latency_sum"] += latency_ms
            self._metrics["usage"]["latency_count"] += 1
            
            if top_score is not None:
                if top_score > 0.7:
                    self._metrics["usage"]["hits_high"] += 1
                elif top_score > 0.4:
                    self._metrics["usage"]["hits_medium"] += 1
                else:
                    self._metrics["usage"]["hits_low"] += 1
            
            self._save_metrics()
    
    # === PROMETHEUS FORMAT ===
    
    def to_prometheus(self) -> str:
        """Exportiert Metriken im Prometheus-Format."""
        lines = []
        
        # Chunks
        lines.append("# HELP stratgen_knowledge_chunks_total Total chunks per collection")
        lines.append("# TYPE stratgen_knowledge_chunks_total gauge")
        for coll, count in self._metrics["chunks"].items():
            lines.append(f'stratgen_knowledge_chunks_total{{collection="{coll}"}} {count}')
        
        # Ingestion
        lines.append("")
        lines.append("# HELP stratgen_ingestion_total Total ingestion operations")
        lines.append("# TYPE stratgen_ingestion_total counter")
        lines.append(f'stratgen_ingestion_total{{status="success"}} {self._metrics["ingestion"]["success"]}')
        lines.append(f'stratgen_ingestion_total{{status="failed"}} {self._metrics["ingestion"]["failed"]}')
        
        lines.append("")
        lines.append("# HELP stratgen_ingestion_duration_seconds_sum Total ingestion duration")
        lines.append("# TYPE stratgen_ingestion_duration_seconds_sum counter")
        lines.append(f'stratgen_ingestion_duration_seconds_sum {self._metrics["ingestion"]["duration_sum"] / 1000}')
        
        # Quality
        lines.append("")
        lines.append("# HELP stratgen_quality_score_avg Average quality score")
        lines.append("# TYPE stratgen_quality_score_avg gauge")
        avg_score = 0.0
        if self._metrics["quality"]["scores_count"] > 0:
            avg_score = self._metrics["quality"]["scores_sum"] / self._metrics["quality"]["scores_count"]
        lines.append(f'stratgen_quality_score_avg {avg_score:.4f}')
        
        lines.append("")
        lines.append("# HELP stratgen_rejected_total Total rejected chunks")
        lines.append("# TYPE stratgen_rejected_total counter")
        lines.append(f'stratgen_rejected_total{{reason="duplicate"}} {self._metrics["quality"]["rejected_duplicate"]}')
        lines.append(f'stratgen_rejected_total{{reason="spam"}} {self._metrics["quality"]["rejected_spam"]}')
        lines.append(f'stratgen_rejected_total{{reason="length"}} {self._metrics["quality"]["rejected_length"]}')
        
        # Usage
        lines.append("")
        lines.append("# HELP stratgen_searches_total Total search operations")
        lines.append("# TYPE stratgen_searches_total counter")
        lines.append(f'stratgen_searches_total {self._metrics["usage"]["searches_total"]}')
        
        lines.append("")
        lines.append("# HELP stratgen_search_latency_avg Average search latency in ms")
        lines.append("# TYPE stratgen_search_latency_avg gauge")
        avg_latency = 0.0
        if self._metrics["usage"]["latency_count"] > 0:
            avg_latency = self._metrics["usage"]["latency_sum"] / self._metrics["usage"]["latency_count"]
        lines.append(f'stratgen_search_latency_avg {avg_latency:.2f}')
        
        lines.append("")
        lines.append("# HELP stratgen_search_hits Total search hits by relevance")
        lines.append("# TYPE stratgen_search_hits counter")
        lines.append(f'stratgen_search_hits{{relevance="high"}} {self._metrics["usage"]["hits_high"]}')
        lines.append(f'stratgen_search_hits{{relevance="medium"}} {self._metrics["usage"]["hits_medium"]}')
        lines.append(f'stratgen_search_hits{{relevance="low"}} {self._metrics["usage"]["hits_low"]}')
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Gibt Metriken als Dict zurück."""
        m = self._metrics
        
        # Berechnete Werte
        avg_quality = 0.0
        if m["quality"]["scores_count"] > 0:
            avg_quality = m["quality"]["scores_sum"] / m["quality"]["scores_count"]
        
        avg_latency = 0.0
        if m["usage"]["latency_count"] > 0:
            avg_latency = m["usage"]["latency_sum"] / m["usage"]["latency_count"]
        
        avg_duration = 0.0
        if m["ingestion"]["total"] > 0:
            avg_duration = m["ingestion"]["duration_sum"] / m["ingestion"]["total"]
        
        return {
            "chunks": {
                "total": sum(m["chunks"].values()),
                "by_collection": m["chunks"]
            },
            "ingestion": {
                "total": m["ingestion"]["total"],
                "success": m["ingestion"]["success"],
                "failed": m["ingestion"]["failed"],
                "success_rate": m["ingestion"]["success"] / max(m["ingestion"]["total"], 1),
                "avg_duration_ms": avg_duration,
                "by_source_type": m["ingestion"]["by_source_type"]
            },
            "quality": {
                "avg_score": avg_quality,
                "total_scored": m["quality"]["scores_count"],
                "rejected": {
                    "duplicate": m["quality"]["rejected_duplicate"],
                    "spam": m["quality"]["rejected_spam"],
                    "length": m["quality"]["rejected_length"],
                    "total": m["quality"]["rejected_duplicate"] + m["quality"]["rejected_spam"] + m["quality"]["rejected_length"]
                }
            },
            "usage": {
                "searches_total": m["usage"]["searches_total"],
                "avg_latency_ms": avg_latency,
                "hit_rate": {
                    "high": m["usage"]["hits_high"],
                    "medium": m["usage"]["hits_medium"],
                    "low": m["usage"]["hits_low"]
                }
            },
            "last_updated": m["last_updated"]
        }


# Singleton
_metrics_instance = None


def get_metrics() -> KnowledgeMetrics:
    """Gibt Singleton Metrics-Instanz zurück."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = KnowledgeMetrics()
    return _metrics_instance
