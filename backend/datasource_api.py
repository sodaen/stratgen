from __future__ import annotations


from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Any, Optional
from services.datasource_store import add_entries, list_entries, delete_entry, get_entries
from services.ds_ingest import ingest_entries, ingest_entries_with_report

from qdrant_client import models as qm
from services.rag_pipeline import get_qdrant, get_embedder, COLL
import numpy as np
from services.rag_pipeline import get_qdrant, get_embedder, COLL, _cosine_rerank
from services.rag_pipeline import _hybrid_rerank as _hybrid_rerank  # optional
from collections import Counter
from services.rag_pipeline import get_qdrant, COLL
from fastapi import Body
from fastapi.responses import JSONResponse
import traceback
import re
from typing import Optional, Any

try:
    from qdrant_client import models as qm  # type: ignore
except Exception:
    import qdrant_client
    qm = qdrant_client.models  # type: ignore[attr-defined]


router = APIRouter(prefix="/datasources", tags=["datasources"])
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryReq(BaseModel):
    customer_name: str = Field(..., description="Kunde (Payload-Feld 'customer')")
    query: str = Field(..., description="Natürlichsprachliche Suchanfrage")
    limit: int = Field(default=5, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optionale Facetten: tokens/topics/subtopics/source_type/title_contains")

# Wir importieren die Implementierung aus ds_ingest
from services.ds_ingest import query_semantic

class Entry(BaseModel):
    type: str  # "file" | "web"
    path: Optional[str] = None
    url: Optional[str] = None
    tokens: list[str] = []
    topics: list[str] = []
    subtopics: list[str] = []

class AddReq(BaseModel):
    customer_name: str
    entries: list[Entry]

@router.post("/add")
def add(req: AddReq):
    ids = add_entries(req.customer_name, [e.model_dump() for e in req.entries])
    return {"ok": True, "ids": ids}


@router.delete("/delete")
def delete(customer_name: str, id: str):
    ok = delete_entry(customer_name, id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}

class IngestReq(BaseModel):
    customer_name: str
    ids: list[str] | None = None  # wenn None → alle

class DsSearchReq(BaseModel):
    customer_name: str
    query: str | None = None
    limit: int = 20
    offset: int = 0

def _normalize_ingest_payload(payload):
    """
    Akzeptiert sowohl Top-Level JSON als auch {"req": {...}}.
    Gibt ein Dict zurück, das direkt in IngestReq(**data) passt.
    """
    if isinstance(payload, dict) and "req" in payload and isinstance(payload["req"], dict):
        return payload["req"]
    return payload

@router.post("/ingest")
def ingest(payload: dict = Body(...)):
    # Normalisiere Body: top-level JSON ODER {'req': {...}}
    data = payload.get('req', payload) if isinstance(payload, dict) else payload
    req = IngestReq(**data)
    """
    Nimmt neue Entries entgegen und legt sie in Qdrant ab.
    - report=True: gibt zusätzlich eine Liste der erzeugten Punkt-IDs zurück
    """
    entries = getattr(req, "entries", None)
    if not entries:
        return {"ok": True, "items": [], "message": "Keine entries übergeben."}

    try:
        # optional: Wrapper nutzen, wenn vorhanden
        try:
            from services.ds_ingest import ingest_entries_with_report
            if report:
                return ingest_entries_with_report(req.customer_name, entries)
        except Exception:
            pass

        from services.ds_ingest import ingest_entries
        return ingest_entries(req.customer_name, entries)
    except Exception as e:
        return {"ok": False, "error": {"code": "INGEST_FAILED", "message": str(e)}}


@router.post("/search")
def ds_search(req: DsSearchReq = Body(...)):
    import traceback
    try:
            from qdrant_client import models as qm
            """
            Scroll-Suche in Qdrant:
            - filtert auf customer_name ODER (Kompat.) customer
            - optionaler Titel-Match
            - liefert items + next_offset
            """
            qdr = get_qdrant()
        
            must = [
                qm.Filter(
                    should=[
                        qm.FieldCondition(key="customer_name", match=qm.MatchValue(value=req.customer_name)),
                        qm.FieldCondition(key="customer",      match=qm.MatchValue(value=req.customer_name)),
                    ]
                )
            ]
            if getattr(req, "title", None):
                must.append(qm.FieldCondition(key="title", match=qm.MatchValue(value=req.title)))
        
            flt = qm.Filter(must=must)
        
            limit = getattr(req, "limit", None) or 10
            offset = getattr(req, "offset", None)
        
            points, next_offset = qdr.scroll(
                collection_name=COLL,
                scroll_filter=flt,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
        
            items = []
            for p in points:
                payload = getattr(p, "payload", None) or {}
                items.append({
                    "id": str(getattr(p, "id", "")),
                    "score": getattr(p, "score", None),
                    "payload": payload,
                    "text": payload.get("text"),
                    "title": payload.get("title"),
                    "customer_name": payload.get("customer_name") or payload.get("customer"),
                })
        
            return {"ok": True, "items": items, "next_offset": next_offset}
    except Exception as e:
        return {"ok": False, "error": {"code": "SERVER_ERROR", "message": str(e), "trace": traceback.format_exc()}}

@router.get("/list")
def ds_list(customer_name: str, limit: int = 50, offset: int = 0):
    return ds_search(DsSearchReq(customer_name=customer_name, limit=limit, offset=offset))

class DsDeleteReq(BaseModel):
    customer_name: str
    title: str | None = None
    ids: list[str] | None = None

@router.post("/delete")
def ds_delete(req: DsDeleteReq):
    import traceback
    try:
            from qdrant_client import models as qm
            qdr = get_qdrant()
            conds = [qm.FieldCondition(key="customer_name", match=qm.MatchValue(value=req.customer_name))]
            if req.title:
                conds.append(qm.FieldCondition(key="title", match=qm.MatchValue(value=req.title)))
            flt = qm.Filter(must=conds)
        
            if req.ids:
                # harte ID-Löschung (primär)
                try:
                    qdr.delete(collection_name=COLL, points_selector=qm.PointIdsList(points=req.ids))
                    return {"ok": True, "deleted_by_ids": len(req.ids)}
                except Exception:
                    # Fallback: Delete via FilterSelector(has_id=...)
                    try:
                        flt_ids = qm.Filter(must=[qm.HasIdCondition(has_id=req.ids)])
                        qdr.delete(collection_name=COLL, points_selector=qm.FilterSelector(filter=flt_ids))
                        return {"ok": True, "deleted_by_ids_filter": len(req.ids)}
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"delete by ids failed: {e}")
        
            # Löschung per Filter
            qdr.delete(collection_name=COLL, points_selector=qm.FilterSelector(filter=flt))
            return {"ok": True, "deleted_by_filter": True}
    except Exception as e:
        return {"ok": False, "error": {"code": "SERVER_ERROR", "message": str(e), "trace": traceback.format_exc()}}

@router.post("/query", tags=["datasources"])
def ds_query(req: QueryReq = Body(...)):
    """
    Semantische Suche über Vektoren; filtert automatisch auf payload['customer'] == req.customer_name.
    Optional: filters = { "tokens": [...], "topics": [...], "subtopics": [...], "source_type": "...", "title_contains": "..." }
    """
    try:
        res = query_semantic(
            customer_name=req.customer_name,
            query=req.query,
            limit=req.limit,
            filters=req.filters or {},
        )

        return res
    except Exception as e:
        return {
            "ok": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "Fehler bei semantischer Suche",
                "details": str(e),
            }
        }

# --- pydantic forward-ref safety (appended once) ---
try:
    from pydantic import BaseModel
    _g = globals()
    for _n, _cls in list(_g.items()):
        if isinstance(_cls, type) and issubclass(_cls, BaseModel):
            _rebuild = getattr(_cls, "model_rebuild", None)
            if callable(_rebuild):
                try:
                    _rebuild()
                except Exception:
                    pass
except Exception:
    pass
# --- end ---

class DsQueryReq(BaseModel):
    customer_name: str
    query: str
    limit: int | None = 5
    filters: dict | None = None  # { "tokens": [...], "topics": [...], "source_type": "..." }

    # Hybrid-Parameter
    hybrid: bool | None = False
    hybrid_pool: int | None = 60
    vector_weight: float | None = 0.6
    lexical_weight: float | None = 0.4
    # filters.tokens_all: list[str]  # alle müssen matchen
    # filters.topics_all: list[str]  # alle müssen matchen
    # filters.date_from: int        # created_ts >=
    # filters.date_to: int          # created_ts <=

    highlight: bool = True  # optionales Snippet zurückgeben
    window: int = 60  # Zeichen links/rechts um ersten Treffer

    offset: int | None = 0  # Pagination: Startindex
    order: str | None = None  # optional: future sorting key

class DsStatsReq(BaseModel):
    customer_name: str
    sample_limit: int | None = 1000  # wie viele Punkte für Facetten-Stichprobe

    ## PAGINATION_PATCH_START
    # Deduplizieren + stabile Sortierung + Pagination
    try:
        _triples: Optional[Any] = []
        for _it in items if 'items' in locals() else []:
            _score: Optional[Any] = _it.get('score', 0.0)
            _id: Optional[Any] = _it.get('id') or (_it.get('payload', {}).get('id'))
            _triples.append((float(_score or 0.0), str(_id) if _id is not None else '', _it))
        _triples.sort(key=lambda t: (-t[0], t[1]))
        _seen: Optional[Any] = set()
        _dedup: Optional[Any] = []
        for _s, _i, _it in _triples:
            if _i and _i not in _seen:
                _seen.add(_i)
                _dedup.append(_it)
        _total: Optional[Any] = len(_dedup)
        _off: Optional[Any] = int(getattr(req, 'offset', 0) or 0)
        _lim: Optional[Any] = int(getattr(req, 'limit', 10) or 10)
        if _off < 0: _off = 0
        if _lim <= 0: _lim = 10
        _slice: Optional[Any] = _dedup[_off:_off+_lim]
        items: Optional[Any] = _slice
        _next: Optional[Any] = _off + len(_slice)
        next_offset: Optional[Any] = _next if _next < _total else None
    except Exception:
        pass
    ## PAGINATION_PATCH_END


@router.post("/stats", summary="Einfache Stats/Facetten pro Kunde")
def ds_stats(req: DsStatsReq = Body(...)):
    """
    Liefert grobe Facetten (source_type, tokens, topics) und Anzahl der Punkte
    für einen Kunden. Zählt auf Basis einer Scroll-Abfrage.
    """
    try:
        qdr = get_qdrant()

        # Filter: Kunde kann entweder in "customer" oder "customer_name" stehen
        must = [
            qm.FieldCondition(key="customer", match=qm.MatchValue(value=req.customer_name)),
            qm.FieldCondition(key="customer_name", match=qm.MatchValue(value=req.customer_name)),
        ]
        qfilter = qm.Filter(should=must)  # should = ODER

        total = 0
        facets = {
            "source_type": Counter(),
            "tokens": Counter(),
            "topics": Counter(),
        }

        # Scrollen (Batches)
        next_page = None
        while True:
            pts, next_page = qdr.scroll(
                collection_name=COLL,
                scroll_filter=qfilter,
                with_payload=True,
                limit=256,
                offset=next_page
            )
            if not pts:
                break

            for p in pts:
                total += 1
                pl = p.payload or {}
                # source_type
                st = pl.get("source_type")
                if isinstance(st, str):
                    facets["source_type"][st] += 1
                # tokens
                toks = pl.get("tokens") or []
                if isinstance(toks, list):
                    for t in toks:
                        if isinstance(t, str):
                            facets["tokens"][t] += 1
                # topics
                tops = pl.get("topics") or []
                if isinstance(tops, list):
                    for t in tops:
                        if isinstance(t, str):
                            facets["topics"][t] += 1

            if next_page is None:
                break

        # Counter -> normale dicts
        out = {
            "ok": True,
            "stats": {
                "total_count": total,
                "sample_size": total,  # hier: gesamte Menge, da wir alles scrollen
                "facets": {
                    "source_type": dict(facets["source_type"]),
                    "tokens": dict(facets["tokens"]),
                    "topics": dict(facets["topics"]),
                },
                "time_range": None,
            }
        }
        return out

    except Exception as e:
        # Saubere Fehlerantwort statt blankem 500
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": str(e)
                }
            }
        )
