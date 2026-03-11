# -*- coding: utf-8 -*-
"""
backend/deep_research_api.py
=============================
Deep Research API – Web-Recherche mit RAG-Integration.

Endpoints:
  POST /research/deep/start                   Neue Session starten
  GET  /research/deep/{session_id}            Session-Details
  GET  /research/deep/{session_id}/stream     Live-Fortschritt (SSE)
  POST /research/deep/{session_id}/ingest     Manuell in Qdrant indexieren
  POST /research/deep/{session_id}/cancel     Session abbrechen
  GET  /research/deep/sessions/list           Alle Sessions
  GET  /research/deep/sessions/stats          Ingest-Statistiken
  POST /research/deep/queries/suggest         Suchanfragen vorschlagen (LLM)

Hinweis: Alle Endpoints prüfen Offline-Modus.
         Bei STRATGEN_OFFLINE=true → 503 mit Erklärung.

Author: StratGen Sprint 5
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/research/deep", tags=["deep_research"])

# ── Offline Guard ─────────────────────────────────────────────────────────────
try:
    from services.offline import is_offline
except ImportError:
    import os
    def is_offline() -> bool:
        return os.getenv("STRATGEN_OFFLINE", "false").lower() == "true"


def _check_online():
    if is_offline():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "offline_mode",
                "message": "Deep Research ist im Offline-Modus nicht verfügbar. "
                           "Setze STRATGEN_OFFLINE=false oder rufe POST /offline/disable auf.",
            }
        )


# ── Request/Response Models ───────────────────────────────────────────────────
class StartResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Thema der Recherche")
    customer_name: str = Field(default="", description="Kundenname für RAG-Kontext")
    queries: list[str] = Field(default=[], description="Optionale eigene Suchanfragen")
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    language: str = Field(default="de", pattern="^(de|en)$")
    auto_ingest: Optional[bool] = Field(default=None, description="Überschreibt RESEARCH_AUTO_INGEST")


class SuggestQueriesRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    language: str = Field(default="de", pattern="^(de|en)$")


# ── Laufende Sessions (In-Memory für Streaming) ───────────────────────────────
_running: dict[str, threading.Thread] = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/start")
def start_research(body: StartResearchRequest):
    """
    Startet eine neue Deep-Research-Session.
    
    Die Session wird sofort gespeichert und im Hintergrund ausgeführt.
    Fortschritt kann via GET /{session_id}/stream verfolgt werden.
    """
    _check_online()

    from services.deep_research import ResearchSession, run_session, save_session, generate_queries
    import os

    session = ResearchSession(
        topic=body.topic,
        customer_name=body.customer_name,
        queries=body.queries or [],
        depth=body.depth,
        language=body.language,
    )

    # Queries vorab generieren damit sie in der Antwort stehen
    if not session.queries:
        try:
            session.queries = generate_queries(body.topic, body.depth, body.language)
        except Exception:
            session.queries = [body.topic]

    # AUTO_INGEST überschreiben falls in Request gesetzt
    import services.deep_research as dr_mod
    original_auto = dr_mod.AUTO_INGEST
    if body.auto_ingest is not None:
        dr_mod.AUTO_INGEST = body.auto_ingest

    save_session(session)

    # Hintergrund-Thread starten
    def _run():
        for _ in run_session(session):
            pass
        dr_mod.AUTO_INGEST = original_auto

    t = threading.Thread(target=_run, daemon=True, name=f"research-{session.session_id}")
    _running[session.session_id] = t
    t.start()

    return JSONResponse({
        "ok": True,
        "session_id": session.session_id,
        "topic": session.topic,
        "queries": session.queries,
        "depth": session.depth,
        "status": "running",
        "stream_url": f"/research/deep/{session.session_id}/stream",
    })


@router.get("/sessions/list")
def list_sessions():
    """Alle Research-Sessions (neueste zuerst)."""
    from services.deep_research import list_sessions as _list
    return JSONResponse({"ok": True, "sessions": _list()})


@router.get("/sessions/stats")
def ingest_stats():
    """Statistiken über in Qdrant indexierte Research-Ergebnisse."""
    from services.research_ingest import get_ingest_stats
    stats = get_ingest_stats()
    return JSONResponse({"ok": True, **stats})


@router.post("/queries/suggest")
def suggest_queries(body: SuggestQueriesRequest):
    """
    LLM generiert optimierte Suchanfragen für ein Thema.
    Nützlich um die Queries vor dem Start anzupassen.
    """
    _check_online()
    from services.deep_research import generate_queries
    queries = generate_queries(body.topic, body.depth, body.language)
    return JSONResponse({"ok": True, "topic": body.topic, "queries": queries})


@router.get("/{session_id}")
def get_session(session_id: str):
    """Details einer Research-Session inkl. aller Ergebnisse."""
    from services.deep_research import load_session
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} nicht gefunden")

    data = session.to_dict()
    # Volltexte nicht in der Übersicht zurückgeben
    for r in data.get("results", []):
        r.pop("full_text", None)

    return JSONResponse({"ok": True, **data})


@router.get("/{session_id}/stream")
def stream_session(session_id: str):
    """
    SSE-Stream: Live-Fortschritt einer laufenden Research-Session.
    
    Events:
      status     – Session-Status geändert
      queries    – Suchanfragen generiert
      query_start – Query startet
      result     – Neues Ergebnis gefunden
      query_done  – Query abgeschlossen + Fortschritt
      done       – Session abgeschlossen
      error      – Fehler aufgetreten
      ingested   – Automatisch in Qdrant indexiert
    """
    from services.deep_research import load_session, run_session, ResearchSession

    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} nicht gefunden")

    # Wenn Session schon done/failed → einmalig Status zurückgeben
    if session.status in ("done", "failed", "cancelled"):
        def _static():
            data = session.to_dict()
            for r in data.get("results", []):
                r.pop("full_text", None)
            yield f"data: {json.dumps({'type': session.status, **data})}\n\n"
        return StreamingResponse(_static(), media_type="text/event-stream")

    def _sse():
        # Neue Session starten falls nicht bereits läuft
        if session_id not in _running or not _running[session_id].is_alive():
            for event in run_session(session):
                yield f"data: {json.dumps(event)}\n\n"
        else:
            # Auf laufende Session pollen
            import time
            while True:
                current = load_session(session_id)
                if not current:
                    break

                # Letzten Stand schicken
                yield f"data: {json.dumps({'type': 'progress', 'status': current.status, 'progress': current.progress, 'result_count': current.result_count})}\n\n"

                if current.status in ("done", "failed", "cancelled"):
                    # Finale Ergebnisse
                    final = current.to_dict()
                    for r in final.get("results", []):
                        r.pop("full_text", None)
                    yield f"data: {json.dumps({'type': current.status, **final})}\n\n"
                    break

                time.sleep(1)

    return StreamingResponse(_sse(), media_type="text/event-stream")


@router.post("/{session_id}/ingest")
def ingest_session(session_id: str):
    """
    Manuell: Research-Ergebnisse in Qdrant knowledge_base indexieren.
    Deduplizierung über URL-Hash (bereits indexierte werden übersprungen).
    """
    from services.deep_research import load_session
    from services.research_ingest import ingest_session as _ingest

    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} nicht gefunden")

    if session.status not in ("done",):
        raise HTTPException(
            status_code=409,
            detail=f"Session ist noch nicht abgeschlossen (status: {session.status})"
        )

    if not session.results:
        return JSONResponse({"ok": True, "ingested": 0, "message": "Keine Ergebnisse zum Indexieren"})

    try:
        count = _ingest(session)
        from services.deep_research import save_session
        session.ingested = True
        session.ingest_count = count
        save_session(session)
        return JSONResponse({"ok": True, "ingested": count, "session_id": session_id})
    except Exception as e:
        log.error("Manual ingest failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/cancel")
def cancel_session(session_id: str):
    """Laufende Research-Session abbrechen."""
    from services.deep_research import load_session, save_session
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} nicht gefunden")

    if session.status not in ("running", "created"):
        return JSONResponse({
            "ok": False,
            "message": f"Session kann nicht abgebrochen werden (status: {session.status})"
        })

    session.status = "cancelled"
    save_session(session)
    return JSONResponse({"ok": True, "session_id": session_id, "status": "cancelled"})
