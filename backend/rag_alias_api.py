"""
RAG Alias API - Aliase für alte Frontend-Pfade
"""
from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/rag", tags=["rag-alias"])


@router.get("/status")
async def rag_status():
    """Alias für /knowledge/admin/status"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:8011/knowledge/admin/status", timeout=10)
            return resp.json()
    except:
        return {"ok": False, "error": "Knowledge service unavailable"}


@router.get("/search")
async def rag_search(q: str = "", limit: int = 5):
    """Alias für /knowledge/admin/search"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://127.0.0.1:8011/knowledge/admin/search?query={q}&limit={limit}",
                timeout=30
            )
            return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}
