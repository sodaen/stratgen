# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from typing import Any, Dict, List
import os, requests

router = APIRouter(prefix="/datasources", tags=["datasources"])

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "stratgen_docs")
EMB_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_embedder = None
def _embed(texts: List[str]) -> List[List[float]]:
    global _embedder
    if _embedder is None:
        # lazy import (schnellerer API-Start)
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMB_MODEL)
    return _embedder.encode(texts, normalize_embeddings=True).tolist()

@router.post("/query")
def query(body: Dict[str,Any] = Body(...)):
    """
    Einheitlicher semantischer Query-Endpunkt gegen Qdrant.
    Eingabe:
      { "query": "...", "customer_name": "...", "limit": 5 }
    Ausgabe:
      { "ok": true, "items": [ { "score": ..., "payload": {...}, "id": ... }, ... ] }
    """
    q = (body or {}).get("query") or ""
    limit = int((body or {}).get("limit") or 5)
    if not q:
        return {"ok": False, "error": "missing 'query'"}

    # 1) Embed Query
    vec = _embed([q])[0]

    # 2) Qdrant-Search (REST)
    try:
        r = requests.post(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search",
            json={"vector": vec, "limit": limit, "with_payload": True},
            timeout=8,
        )
        r.raise_for_status()
        jr = r.json() or {}
        res = jr.get("result") or []
    except Exception as e:
        return {"ok": False, "error": f"qdrant search failed: {type(e).__name__}: {e}"}

    # 3) Ausgabeliste vereinheitlichen
    items: List[Dict[str,Any]] = []
    for hit in res:
        items.append({
            "id": hit.get("id"),
            "score": hit.get("score"),
            "payload": hit.get("payload") or {},
        })
    return {"ok": True, "items": items}
