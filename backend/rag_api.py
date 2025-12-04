"""
RAG & Knowledge API für Stratgen.
Endpoints für Knowledge Base Status und Suche.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status")
async def get_rag_status():
    """Detaillierter RAG-System Status."""
    try:
        from services.unified_knowledge import get_stats
        stats = get_stats()
        
        return {
            "ok": True,
            "rag": {
                "qdrant": stats.get("qdrant_available", False),
                "embedder": stats.get("embedder_available", False),
                "vision": stats.get("vision_available", False)
            },
            "collections": stats.get("collections", {}),
            "directories": stats.get("directories", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/search")
async def search_knowledge(q: str, limit: int = 5):
    """Suche in der Knowledge Base."""
    try:
        from services.unified_knowledge import search
        results = search(q, limit)
        return {
            "ok": True,
            "query": q,
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.text_content[:300] if r.text_content else "",
                    "source": r.source
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/ingest")
async def ingest_file(file_path: str):
    """Indexiert eine Datei in die Knowledge Base."""
    try:
        from services.unified_knowledge import ingest_file
        result = ingest_file(file_path)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
