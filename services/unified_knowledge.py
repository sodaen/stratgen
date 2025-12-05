"""
Unified Knowledge Service für Stratgen.
Kombiniert Text-RAG (Qdrant) mit Vision-Analyse (Moondream).
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Verzeichnis-Konfiguration

def _log_search_metrics(query: str, results: list, latency_ms: float):
    """Loggt Search-Metriken für Analytics."""
    try:
        import httpx
        scores = [r.score for r in results if hasattr(r, 'score')]
        httpx.post(
            "http://localhost:8011/admin/metrics/search/log",
            json={
                "query": query[:200],
                "results_count": len(results),
                "top_score": max(scores) if scores else 0,
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "latency_ms": latency_ms
            },
            timeout=2.0
        )
    except:
        pass  # Logging sollte nie die Hauptfunktion blockieren


DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
RAW_DIR = DATA_ROOT / "raw"           # Master-Präsentationen
KNOWLEDGE_DIR = DATA_ROOT / "knowledge"  # Dokumente, PDFs
UPLOADS_DIR = DATA_ROOT / "uploads"      # User-Uploads
EXPORTS_DIR = DATA_ROOT / "exports"      # Generierte Decks


@dataclass
class KnowledgeItem:
    """Ein Wissens-Element aus dem System."""
    id: str
    source: str
    content_type: str  # text, visual, combined
    text_content: Optional[str] = None
    visual_features: Optional[Dict] = None
    metadata: Optional[Dict] = None
    score: float = 0.0


class UnifiedKnowledge:
    """Unified Knowledge Manager - kombiniert Text und Vision."""
    
    def __init__(self):
        self._qdrant = None
        self._embedder = None
        self._vision = None
        self._initialized = False
    
    def _init_services(self):
        """Lazy initialization der Services."""
        if self._initialized:
            return
        
        try:
            from services.rag_pipeline import get_qdrant, get_embedder
            self._qdrant = get_qdrant()
            self._embedder = get_embedder()
        except Exception as e:
            logger.warning(f"RAG services nicht verfügbar: {e}")
        
        try:
            from services.vision_analyzer import is_available, analyze_image
            if is_available():
                self._vision = analyze_image
        except Exception as e:
            logger.warning(f"Vision service nicht verfügbar: {e}")
        
        self._initialized = True
    
    def search(self, query: str, limit: int = 5, include_visual: bool = True) -> List[KnowledgeItem]:
        """
        Sucht in der Knowledge Base (Text + optional Visual).
        """
        self._init_services()
        results = []
        
        # Text-Suche in Qdrant
        if self._qdrant and self._embedder:
            try:
                vec = self._embedder.encode(query).tolist()
                hits = self._qdrant.search(
                    collection_name="stratgen_docs",
                    query_vector=vec,
                    limit=limit
                )
                
                for hit in hits:
                    payload = hit.payload or {}
                    results.append(KnowledgeItem(
                        id=str(hit.id),
                        source=payload.get("source", "unknown"),
                        content_type="text",
                        text_content=payload.get("text", ""),
                        metadata=payload,
                        score=hit.score
                    ))
            except Exception as e:
                logger.error(f"Qdrant search failed: {e}")
        
        return results
    
    def search_for_slide(self, slide_type: str, slide_title: str, 
                         brief: str = "", context: Dict = None) -> Dict[str, Any]:
        """
        Spezialisierte Suche für Slide-Generierung.
        Kombiniert Text-Knowledge mit Visual-Templates.
        """
        self._init_services()
        
        # Baue optimierte Suchqueries
        queries = self._build_slide_queries(slide_type, slide_title, brief, context)
        
        text_results = []
        visual_templates = []
        
        # Text-Suche
        for query in queries[:3]:
            results = self.search(query, limit=3, include_visual=False)
            for r in results:
                if r.score >= 0.5 and r.text_content:
                    text_results.append({
                        "text": r.text_content[:500],
                        "source": r.source,
                        "score": r.score
                    })
        
        # Deduplizieren
        seen = set()
        unique_results = []
        for r in text_results:
            key = r["text"][:100]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return {
            "ok": True,
            "text_results": unique_results[:5],
            "visual_templates": visual_templates[:3],
            "queries_used": queries
        }
    
    def _build_slide_queries(self, slide_type: str, title: str, 
                             brief: str, context: Dict = None) -> List[str]:
        """Baut optimierte Suchqueries für einen Slide."""
        queries = []
        context = context or {}
        industry = context.get("industry", "")
        
        # Type-spezifische Keywords
        type_keywords = {
            "problem": ["Challenge", "Problem", "Pain Points", "Issues"],
            "solution": ["Solution", "Approach", "Strategy", "How to"],
            "benefits": ["Benefits", "Advantages", "Value", "ROI"],
            "roi": ["ROI", "Business Case", "Metrics", "KPI"],
            "roadmap": ["Roadmap", "Timeline", "Implementation", "Phases"],
            "competitive": ["Competitive", "Comparison", "Benchmark"],
            "case_study": ["Case Study", "Success Story", "Example"],
            "data": ["Data", "Statistics", "Research", "Insights"],
            "executive_summary": ["Strategy", "Overview", "Summary"],
            "next_steps": ["Next Steps", "Action", "Recommendations"],
        }
        
        keywords = type_keywords.get(slide_type, ["Strategy", "Business"])
        
        # Query-Kombinationen
        for kw in keywords[:2]:
            if title:
                queries.append(f"{title} {kw}")
            if industry:
                queries.append(f"{industry} {kw}")
        
        # Allgemeine Queries
        queries.append(f"GTM {slide_type}")
        queries.append(f"Marketing {slide_type}")
        
        if brief:
            # Extrahiere wichtige Begriffe aus dem Brief
            brief_words = [w for w in brief.split()[:20] if len(w) > 4]
            if brief_words:
                queries.append(" ".join(brief_words[:5]))
        
        return queries[:6]
    
    def analyze_visual(self, image_path: str) -> Dict[str, Any]:
        """Analysiert ein Bild mit dem Vision-Modell."""
        self._init_services()
        
        if not self._vision:
            return {"ok": False, "error": "Vision service nicht verfügbar"}
        
        return self._vision(image_path)
    
    def ingest_file(self, file_path: str, analyze_visuals: bool = True) -> Dict[str, Any]:
        """
        Indexiert eine Datei (Text + optional visuelle Analyse).
        """
        from services.ds_ingest import ingest_entry
        
        path = Path(file_path)
        ext = path.suffix.lower()
        
        result = {"ok": False, "text_chunks": 0, "visual_features": None}
        
        # Text-Indexierung
        try:
            entry = {"path": str(path), "type": "file", "source": str(path)}
            ingest_result = ingest_entry("stratgen_docs", entry)
            result["text_chunks"] = ingest_result.get("count", 0)
            result["ok"] = ingest_result.get("ok", False)
        except Exception as e:
            logger.error(f"Text ingest failed: {e}")
        
        # Visuelle Analyse für Präsentationen/Bilder
        if analyze_visuals and ext in (".pptx", ".png", ".jpg", ".jpeg"):
            if self._vision:
                try:
                    if ext == ".pptx":
                        from services.vision_analyzer import analyze_presentation_template
                        visual_result = analyze_presentation_template(str(path))
                    else:
                        visual_result = self.analyze_visual(str(path))
                    result["visual_features"] = visual_result
                except Exception as e:
                    logger.warning(f"Visual analysis failed: {e}")
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Knowledge Base zurück."""
        self._init_services()
        
        stats = {
            "qdrant_available": self._qdrant is not None,
            "embedder_available": self._embedder is not None,
            "vision_available": self._vision is not None,
            "collections": {},
            "directories": {}
        }
        
        # Qdrant Stats
        if self._qdrant:
            try:
                for coll in ["stratgen_docs", "strategies"]:
                    info = self._qdrant.get_collection(coll)
                    stats["collections"][coll] = {
                        "points": info.points_count,
                        "status": info.status.value if hasattr(info.status, 'value') else str(info.status)
                    }
            except Exception as e:
                logger.warning(f"Could not get Qdrant stats: {e}")
        
        # Directory Stats
        for name, path in [("raw", RAW_DIR), ("knowledge", KNOWLEDGE_DIR), 
                           ("uploads", UPLOADS_DIR), ("exports", EXPORTS_DIR)]:
            if path.exists():
                files = list(path.rglob("*"))
                stats["directories"][name] = {
                    "path": str(path),
                    "files": len([f for f in files if f.is_file()]),
                    "size_mb": sum(f.stat().st_size for f in files if f.is_file()) / (1024*1024)
                }
        
        return stats


# Singleton-Instanz
_unified_knowledge = None

def get_unified_knowledge() -> UnifiedKnowledge:
    """Gibt die Singleton-Instanz zurück."""
    global _unified_knowledge
    if _unified_knowledge is None:
        _unified_knowledge = UnifiedKnowledge()
    return _unified_knowledge


# Convenience-Funktionen
def search(query: str, limit: int = 5) -> List[KnowledgeItem]:
    return get_unified_knowledge().search(query, limit)

def search_for_slide(slide_type: str, slide_title: str, brief: str = "", context: Dict = None) -> Dict:
    return get_unified_knowledge().search_for_slide(slide_type, slide_title, brief, context)

def get_stats() -> Dict:
    return get_unified_knowledge().get_stats()

def ingest_file(file_path: str) -> Dict:
    return get_unified_knowledge().ingest_file(file_path)
