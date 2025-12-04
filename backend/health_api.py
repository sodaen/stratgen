
# === RAG & Knowledge Status ===
@router.get("/rag/status")
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

@router.get("/rag/search")
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
