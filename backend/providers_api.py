# -*- coding: utf-8 -*-

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional

from services.providers import statista, brandwatch, talkwalker
from services.providers.common import normalize_entry
from services.datasource_store import add_entries as ds_add_entries
try:
    from services.ds_ingest import ingest_entries as ds_ingest_entries
except Exception:
    ds_ingest_entries = None  # optional

router = APIRouter(prefix="/providers", tags=["providers"])

def _registry() -> Dict[str, Any]:
    return {"statista": statista, "brandwatch": brandwatch, "talkwalker": talkwalker}

@router.get("/status")
def status():
    reg = _registry()
    st = [reg[name].status() for name in sorted(reg.keys())]
    return {"ok": True, "providers": st}

@router.post("/pull")
def pull(
    provider: str = Query(..., min_length=3),
    customer_name: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    query: Optional[str] = Query(None),
    embed: int = Query(0, ge=0, le=1),
):
    reg = _registry()
    if provider not in reg:
        raise HTTPException(status_code=400, detail=f"unknown provider '{provider}'")
    mod = reg[provider]
    st = mod.status()
    if not st.get("configured"):
        return {"ok": False, "provider": provider, "configured": False, "missing": st.get("missing", [])}

    raw_items = mod.pull_recent(customer_name=customer_name, limit=limit, query=query)
    entries = [
        normalize_entry(
            customer_name=customer_name,
            title=i.get("title") or "(untitled)",
            text=i.get("text") or "",
            source_type=provider,
            canonical_url=i.get("canonical_url"),
            topics=i.get("topics") or [],
            meta={"query": query} if query else {},
        )
        for i in raw_items
    ]

    inserted = 0
    if entries:
        ds_add_entries(customer_name, entries)
        inserted = len(entries)

    embed_res: Dict[str, Any] = {"ok": False, "embedded": 0}
    if embed and entries:
        try:
            if ds_ingest_entries:
                er = ds_ingest_entries(entries)  # kein 'model' Parameter hier
                if isinstance(er, dict):
                    embed_res = {"ok": bool(er.get("ok", True)), "embedded": int(er.get("embedded", 0))}
                else:
                    embed_res = {"ok": True}
            else:
                embed_res = {"ok": False, "error": "embedding pipeline not available"}
        except Exception as e:
            embed_res = {"ok": False, "error": str(e), "embedded": 0}

    return {"ok": True, "provider": provider, "configured": True, "inserted": inserted, "embed": embed_res}
