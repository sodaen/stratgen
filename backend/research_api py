# backend/research_api.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
import hashlib, time

# vorhandene Services (deine Infrastruktur):
from services.rag_pipeline import get_qdrant, COLL, get_embedder
from services.datasource_store import add_entries  # schreibt "entries" in deinen Store (IDs zurück)

router = APIRouter(prefix="/research", tags=["research"])

# ---------- Datenmodelle ----------

class SourceSpec(BaseModel):
    """Ein 'Quellenauftrag'. Entweder URL, oder API-Connector, oder bereits hochgeladene Datei-ID."""
    kind: Literal["url", "api", "file_id"] = Field(..., description="Quelle: url|api|file_id")
    value: str = Field(..., description="URL / API-Connector-Key / File-ID")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Optional: Hinweise (z.B. seed-topic, language)")

class AddSourcesReq(BaseModel):
    customer_name: str
    sources: List[SourceSpec]

class CrawlReq(BaseModel):
    customer_name: str
    limit: int = 25
    # Filter, welche Quellen-typen genutzt werden:
    include_kinds: Optional[List[str]] = None  # z.B. ["url","api","file_id"]
    # Für API-Connectoren: welche Provider?
    connectors: Optional[List[str]] = None     # z.B. ["brandwatch","talkwalker","statista"]

class InsightsReq(BaseModel):
    customer_name: str
    query: str
    top_k: int = 12

# ---------- Datei-Upload (Nutzerpfad) ----------

@router.post("/files/upload")
async def upload_file(customer_name: str, f: UploadFile = File(...)):
    """
    Nimmt eine Datei an, extrahiert Text (hier Stub), erzeugt Entry und legt ab.
    In echt: PDF/Docx/HTML → Text; NER/Tagging → tokens/topics/subtopics/…
    """
    raw = await f.read()
    text = raw.decode(errors="ignore") if raw else ""
    if not text.strip():
        raise HTTPException(400, "Leere Datei oder nicht lesbar")

    # Minimaler Entry (du kannst hier deine Pipeline aufrufen)
    entry = {
        "type": "file",
        "path": f.filename,
        "tokens": [],
        "topics": [],
        "subtopics": [],
        "text": text,
        "customer_name": customer_name,
        "source_type": "file",
        "canonical_url": None,
        "pub_date_ts": int(time.time()),
        "hash": hashlib.sha1(raw).hexdigest() if raw else hashlib.sha1(text.encode()).hexdigest(),
    }
    ids = add_entries(customer_name, [entry])
    return {"ok": True, "ids": ids}

# ---------- Quellen registrieren (URLs / API / File-IDs) ----------

@router.post("/sources/add")
def add_sources(req: AddSourcesReq):
    """
    Registriert Quellen. Für file_id: referenziere zuvor hochgeladene/ingestete Files.
    Für url/api: werden in /research/crawl verarbeitet.
    """
    # Wir speichern die "Aufträge" als Entries (lightweight) – oder extern in Redis/DB.
    entries = []
    for s in req.sources:
        entries.append({
            "type": s.kind,           # "url" | "api" | "file_id"
            "path": s.value if s.kind != "api" else None,
            "url": s.value if s.kind == "url" else None,
            "tokens": s.meta.get("tokens", []),
            "topics": s.meta.get("topics", []),
            "subtopics": s.meta.get("subtopics", []),
            "meta": s.meta,
            "customer_name": req.customer_name,
            "source_type": s.kind,
            "text": None,
            "canonical_url": s.meta.get("canonical_url"),
            "pub_date_ts": s.meta.get("pub_date_ts"),
            "hash": hashlib.sha1(f"{s.kind}:{s.value}".encode()).hexdigest(),
        })
    ids = add_entries(req.customer_name, entries)
    return {"ok": True, "registered": len(ids), "ids": ids}

# ---------- Crawl / Fetch (URL + API-Connectoren) ----------

@router.post("/crawl")
def crawl(req: CrawlReq):
    """
    Lädt Inhalte aus registrierten Quellen:
      - URLs (HTTP fetch + parse → Text)
      - API-Connectoren (brandwatch/talkwalker/statista/…)
      - file_id (optional: Metadaten anreichern / re-index)
    Ergebnis wird als Einträge in Qdrant/Data-Store abgelegt.
    """
    # Stub: Hier rufst du deine Connector-Schicht auf (siehe unten: services/connectors).
    # Beispiel: from services.connectors import run_crawl
    try:
        from services.connectors import run_crawl
    except Exception:
        # Minimaler Fallback (kein echter Crawl)
        return {"ok": True, "fetched": 0, "note": "Connector-Schicht (services.connectors) noch Stub."}

    stats = run_crawl(
        customer_name=req.customer_name,
        limit=req.limit,
        include_kinds=req.include_kinds,
        connectors=req.connectors,
    )
    return {"ok": True, "fetched": stats.get("fetched", 0), "details": stats}

# ---------- Insights / RAG-Extrakte ----------

@router.post("/insights")
def insights(req: InsightsReq):
    """
    Holt Top-K Fundstellen aus Qdrant und erzeugt kurze Bullet-Insights mit Quellenangaben.
    """
    qdr = get_qdrant()
    emb = get_embedder()
    vec = emb.embed(req.query)

    # sehr einfacher Vector-Query; optional Hybrid nachrüsten (du hast _hybrid_rerank)
    from qdrant_client import models as qm
    filt = qm.Filter(
        should=[
            qm.FieldCondition(key="customer_name", match=qm.MatchValue(value=req.customer_name)),
            qm.FieldCondition(key="customer", match=qm.MatchValue(value=req.customer_name)),
        ]
    )
    res = qdr.search(
        collection_name=COLL,
        query_vector=vec,
        limit=req.top_k,
        with_payload=True,
        query_filter=filt,
    )

    bullets = []
    for p in res:
        pl = p.payload or {}
        bullets.append({
            "point_id": str(getattr(p, "id", "")),
            "text_snippet": (pl.get("text") or "")[:280],
            "source_type": pl.get("source_type"),
            "title": pl.get("title"),
            "canonical_url": pl.get("canonical_url"),
        })

    return {
        "ok": True,
        "query": req.query,
        "top_k": req.top_k,
        "bullets": bullets
    }

