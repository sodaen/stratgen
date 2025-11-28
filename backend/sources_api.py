from __future__ import annotations


# -----------------------------------------------------------------------------
# Sources API
# - /sources/register  : Quellen registrieren (Batch-Dedup innerhalb desselben Calls)
# - /sources/list      : alle Quellen
# - /sources/{id}      : Einzelquelle
# - Legacy-Aliasse:
#     /sources/data/register, /sources/data/list, /sources/data/remove
# -----------------------------------------------------------------------------

from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Body, HTTPException, Path
from pydantic import BaseModel, Field
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from uuid import uuid4

router = APIRouter(prefix="/sources", tags=["sources"])

# --- In-Memory-Store (einfach & ausreichend für jetzt) -----------------------
# Hinweis: Prozess-lokale Persistenz. Für echte Persistenz später DB/Service.
_SOURCES: Dict[str, Dict[str, Any]] = {}           # id -> source dict
_URL_INDEX: Dict[str, str] = {}                     # canonical_url -> id

# --- Modelle -----------------------------------------------------------------
class SourceItem(BaseModel):
    type: Literal["url", "text", "file"] = "url"
    url: Optional[str] = None
    title: Optional[str] = None
    provider: Optional[str] = None

class RegisterReq(BaseModel):
    customer_name: str
    items: List[SourceItem]

class RegisterResp(BaseModel):
    ok: bool = True
    created: List[Dict[str, Any]] = Field(default_factory=list)
    deduped: bool = False  # true, wenn innerhalb des Batches oder ggü. Bestand dedupliziert wurde

class ListResp(BaseModel):
    ok: bool = True
    sources: List[Dict[str, Any]]

class GetResp(BaseModel):
    ok: bool = True
    source: Optional[Dict[str, Any]] = None

class RemoveReq(BaseModel):
    id: str

class RemoveResp(BaseModel):
    ok: bool = True
    removed: bool = False

# --- URL-Normalisierung ------------------------------------------------------
def normalize_url(raw: str) -> str:
    """
    Normalisiert URLs kanonisch:
    - Scheme -> https (falls http/https; andere Schemes bleiben erhalten)
    - Host -> lowercase
    - Path -> lowercase (damit /Report == /report, wie in deinem Test)
    - Query -> Schlüssel sortiert; Duplikate in stabiler Reihenfolge
    - Fragmente entfernt
    """
    try:
        sp = urlsplit(raw.strip())
    except Exception:
        return raw

    scheme = sp.scheme.lower()
    if scheme in ("http", "https"):
        scheme = "https"

    netloc = sp.netloc.lower()
    path = (sp.path or "").lower()

    # Query sortieren (stabil)
    q_pairs = parse_qsl(sp.query, keep_blank_values=True)
    q_pairs.sort(key=lambda kv: kv[0])
    query = urlencode(q_pairs, doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))

# --- Kern-Endpunkte ----------------------------------------------------------
@router.post("/register", response_model=RegisterResp)
def register(req: RegisterReq = Body(...)):
    """
    Registriert Quellen. Batch-Dedup findet *innerhalb dieses Requests* statt,
    zusätzlich wird gegen den bestehenden Store dedupliziert.
    """
    created: List[Dict[str, Any]] = []
    dedup_happened = False

    # 1) Batch-Dedup: gleiche URL im selben Call nur einmal aufnehmen
    seen_keys = set()
    batch_items: List[SourceItem] = []
    for it in req.items:
        if it.type == "url" and it.url:
            c = normalize_url(it.url)
            key = f"url::{c}"
        else:
            # Für text/file könnte man eigene Schlüssel ableiten; hier simple Heuristik
            key = f"{it.type}::{(it.url or it.title or '')}".strip()

        if key in seen_keys:
            dedup_happened = True
            continue
        seen_keys.add(key)
        batch_items.append(it)

    # 2) Gegen Bestand deduplizieren & neu anlegen
    for it in batch_items:
        if it.type == "url" and it.url:
            c = normalize_url(it.url)
            # bereits im Store?
            if c in _URL_INDEX:
                dedup_happened = True
                continue

            sid = str(uuid4())
            doc = {
                "id": sid,
                "type": "url",
                "url": c,
                "title": it.title,
                "provider": it.provider,
            }
            _SOURCES[sid] = doc
            _URL_INDEX[c] = sid
            created.append(doc)

        else:
            # einfache Ablage für text/file (hier ohne echte Datei-Verarbeitung)
            sid = str(uuid4())
            doc = {
                "id": sid,
                "type": it.type,
                "url": it.url,
                "title": it.title,
                "provider": it.provider,
            }
            _SOURCES[sid] = doc
            created.append(doc)

    return RegisterResp(ok=True, created=created, deduped=dedup_happened)

@router.get("/list", response_model=ListResp)
def list_sources():
    return ListResp(ok=True, sources=list(_SOURCES.values()))

@router.get("/{source_id}", response_model=GetResp)
def get_source(source_id: str = Path(..., description="ID einer Quelle")):
    src = _SOURCES.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return GetResp(ok=True, source=src)

# --- Legacy-Aliasse ----------------------------------------------------------
# 1) /sources/data/register -> identisches Verhalten wie /sources/register
@router.post("/data/register", response_model=RegisterResp)
def legacy_register(req: RegisterReq = Body(...)):
    return register(req)  # Delegation

# 2) /sources/data/list
@router.get("/data/list", response_model=ListResp)
def legacy_list():
    return list_sources()

# 3) /sources/data/remove
@router.post("/data/remove", response_model=RemoveResp)
def legacy_remove(req: RemoveReq = Body(...)):
    sid = req.id
    if sid in _SOURCES:
        doc = _SOURCES.pop(sid)
        if doc.get("type") == "url" and doc.get("url"):
            _URL_INDEX.pop(doc["url"], None)
        return RemoveResp(ok=True, removed=True)
    return RemoveResp(ok=True, removed=False)
