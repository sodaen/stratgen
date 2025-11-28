# -*- coding: utf-8 -*-

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from pathlib import Path
import time, hashlib, uuid

# JSON-Store für Rohquellen
from services.datasource_store import add_entries as ds_add_entries

# Vektor-Ingest (optional verfügbar)
try:
    from services import ds_ingest  # erwartet ingest_entries(customer, entries)
except Exception:  # pragma: no cover
    ds_ingest = None  # type: ignore

router = APIRouter(prefix="/research", tags=["research"])

@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    customer_name: str = Query(..., alias="customer_name"),
    embed: int = Query(0, ge=0, le=1),
    model: str | None = Query(None, description="nur zur Anzeige; wird NICHT an ds_ingest durchgereicht")
):
    ts = int(time.time())
    # Datei speichern
    up_dir = Path("data/raw/uploads"); up_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{ts}____{file.filename}"
    dest = up_dir / safe_name
    raw = await file.read()
    dest.write_bytes(raw)

    # Basismetadaten + Text für Store
    text = raw.decode("utf-8", errors="ignore")
    eid = str(uuid.uuid4())
    entry = {
        "id": eid,
        "type": "file",
        "path": str(dest),
        "text": text,
        "tokens": [],
        "topics": [],
        "subtopics": [],
        "customer_name": customer_name,
        "source_type": "file",
        "canonical_url": None,
        "pub_date_ts": ts,
        "hash": hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest(),
        "title": file.filename,
    }

    # 1) Immer im JSON-Store registrieren
    ds_add_entries(customer_name, [entry])

    # 2) Optional: Vektor-Ingest (KEIN 'model' Keyword übergeben!)
    embed_resp: dict
    if embed and ds_ingest:
        try:
            r = ds_ingest.ingest_entries(customer_name, [entry])  # <- nur (customer, entries)
            embed_resp = {"ok": bool(r.get("ok", True)), **r}
        except Exception as e:  # Qdrant/Embedder nicht verfügbar → soft fail
            embed_resp = {"ok": False, "error": str(e)}
    else:
        embed_resp = {"ok": False, "embedded": 0}

    return JSONResponse({
        "ok": True,
        "customer": customer_name,
        "stored_path": str(dest),
        "id": eid,
        "tokens": len(text.split()),
        "embed": embed_resp,
        "note": "Parameter 'model' wird akzeptiert (UI/Hinweis), aber NICHT an ds_ingest übergeben."
    })
