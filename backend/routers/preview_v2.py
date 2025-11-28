from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.routers.knowledge_search_v2 import search_semantic_v2_local

router = APIRouter(tags=["content"])

class PreviewRequest(BaseModel):
    project_id: Optional[str] = None
    topic: Optional[str] = None
    k: int = 6
    debug: bool = False

@router.post("/content/preview_with_sources_v2", operation_id="content_preview_with_sources_v2")
def preview_with_sources_v2(req: PreviewRequest):
    query = (req.topic or (f"project {req.project_id}" if req.project_id else "")).strip() or "strategy preview"

    citations: List[Dict] = []
    dedup_count: int = 0
    debug_info: Dict = {}

    try:
        res = search_semantic_v2_local(q=query, k=req.k, dedup=True, with_snippets=True, rerank=True, snippet_bytes=280, debug=req.debug)
        base_total = res.get("total", 0)
        for r in res.get("results", [])[:req.k]:
            citations.append({
                "path": r.get("path"),
                "score": r.get("score"),
                "title": r.get("title"),
                "snippet": r.get("snippet"),
            })
        dedup_count = max(0, base_total - len(citations))
        if req.debug and isinstance(res.get("debug"), dict):
            debug_info = res["debug"]
    except Exception:
        pass

    outline = {
        "title": "Auto-Preview",
        "sections": [
            {"title": "Einleitung", "bullets": ["Zielsetzung", "Kontext"]},
            {"title": "Kernpunkte", "bullets": ["These A", "These B", "These C"]},
        ],
    }
    diagnostics = {
        "citations_count": len(citations),
        "retrieval_k": req.k,
        "rerank_enabled": True,
        "dedup_count": dedup_count,
        "extra": {"query": query, **({"debug": debug_info} if req.debug else {})},
    }
    return {"outline": outline, "bullets": None, "citations": citations, "diagnostics": diagnostics}
