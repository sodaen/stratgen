from __future__ import annotations

from typing import List, Dict, Any, Tuple
from fastapi import APIRouter, Body
from services.knowledge_graph import upsert_nodes, upsert_edges, search as kg_search, stats as kg_stats

router = APIRouter(prefix="/graph", tags=["graph"])

@router.post("/upsert/nodes")
def upsert_nodes_api(nodes: List[Dict[str, Any]] = Body(...)):
    return {"ok": True, "inserted": upsert_nodes(nodes)}

@router.post("/upsert/edges")
def upsert_edges_api(edges: List[Tuple[str,str,str]] = Body(..., example=[["Brand","competes","Competitor A"]])):
    return {"ok": True, "inserted": upsert_edges(edges)}

@router.get("/search")
def search_api(q: str):
    return kg_search(q)

@router.get("/stats")
def stats_api():
    return kg_stats()
