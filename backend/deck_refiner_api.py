# -*- coding: utf-8 -*-
"""
backend/deck_refiner_api.py
============================
Iterativer Multi-LLM Deck-Refinement API.

Endpoints:
  POST /refine/deck/start         Refinement starten (Hintergrund)
  GET  /refine/deck/{id}/stream   Live-Fortschritt (SSE)
  GET  /refine/deck/{id}          Ergebnis abrufen
  POST /refine/deck/{id}/export   Verfeinerte Slides → PPTX exportieren
  GET  /refine/deck/sessions      Alle Sessions
  GET  /refine/config             Aktuelle Refiner-Konfiguration

Author: StratGen Sprint 9
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/refine", tags=["deck_refiner"])

SESSION_DIR = Path(os.getenv("REFINER_SESSION_DIR", "data/refiner"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)

_running: dict[str, threading.Thread] = {}
_sessions: dict[str, dict] = {}   # In-Memory Cache


# ── Request Models ────────────────────────────────────────────────────────────

class StartRefineRequest(BaseModel):
    briefing: str = Field(..., min_length=20,
                          description="Detailliertes Briefing für das Deck")
    customer_name: str = Field(default="", description="Kundenname")
    deck_size: int = Field(default=10, ge=4, le=25)

    # Generator-LLM (erstellt Slides)
    generator_provider: str = Field(default="ollama",
                                     description="ollama | openai | anthropic | nemotron")
    generator_model: str | None = Field(default="llama3:8b",
                                         description="Modell für Generierung (kreativer, stärker)")

    # Critic-LLM (bewertet Slides — DeepSeek-R1 empfohlen für Reasoning)
    critic_provider: str = Field(default="ollama",
                                  description="ollama | openai | anthropic | nemotron")
    critic_model: str | None = Field(default="deepseek-r1:8b",
                                      description="Critic-Modell (DeepSeek-R1 für Reasoning empfohlen)")

    # Struktur-LLM (Agenda, JSON-Output — Qwen2.5 empfohlen)
    structure_provider: str = Field(default="ollama",
                                     description="Provider für strukturierten Output")
    structure_model: str | None = Field(default="qwen2.5:7b",
                                         description="Struktur-Modell (Qwen2.5 für JSON empfohlen)")

    # Qualitätsziele
    quality_threshold: float = Field(default=8.0, ge=5.0, le=10.0,
                                      description="Durchschnittlicher Score zum Stoppen")
    max_iterations: int = Field(default=3, ge=1, le=5,
                                 description="Maximale Verbesserungsrunden")


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _save_session(session_id: str, data: dict) -> None:
    _sessions[session_id] = data
    (SESSION_DIR / f"{session_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _load_session(session_id: str) -> dict | None:
    if session_id in _sessions:
        return _sessions[session_id]
    p = SESSION_DIR / f"{session_id}.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _sessions[session_id] = data
            return data
        except Exception:
            pass
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/config")
def get_config():
    """Aktuelle Refiner-Konfiguration aus ENV-Variablen."""
    from services.llm_router import get_active_provider, list_providers
    return JSONResponse({
        "ok": True,
        "defaults": {
            "quality_threshold": float(os.getenv("REFINER_QUALITY_THRESHOLD", "8.0")),
            "max_iterations":    int(os.getenv("REFINER_MAX_ITERATIONS", "3")),
            "min_slide_score":   float(os.getenv("REFINER_MIN_SLIDE_SCORE", "6.0")),
        },
        "active_provider": get_active_provider(),
        "all_providers": list_providers(),
        "tip": (
            "Generator = kreatives LLM (Ollama/Mistral empfohlen). "
            "Critic = kritisches LLM (Nemotron empfohlen für anderen Blickwinkel). "
            "Beide können gleich sein wenn nur ein Provider verfügbar ist."
        ),
    })


@router.get("/sessions")
def list_sessions():
    """Alle Refinement-Sessions."""
    sessions = []
    for p in sorted(SESSION_DIR.glob("*.json"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append({
                "session_id":    data.get("session_id"),
                "status":        data.get("status"),
                "avg_score":     data.get("avg_score", 0),
                "iterations":    data.get("iteration", 0),
                "total_slides":  len(data.get("slides", [])),
                "customer_name": data.get("customer_name"),
                "briefing":      (data.get("briefing") or "")[:80] + "...",
                "generator":     data.get("generator_provider"),
                "critic":        data.get("critic_provider"),
            })
        except Exception:
            pass
    return JSONResponse({"ok": True, "sessions": sessions})


@router.post("/deck/start")
def start_refine(body: StartRefineRequest):
    """
    Startet einen iterativen Deck-Refinement-Prozess.

    Der Prozess läuft im Hintergrund.
    Live-Fortschritt via GET /refine/deck/{session_id}/stream verfolgen.
    """
    from services.deck_refiner import RefineSession, refine_deck
    from services.llm_router import get_model

    # Generator-Modell bestimmen
    gen_model = body.generator_model or get_model(body.generator_provider)

    # Critic-Modell bestimmen
    crit_model = body.critic_model or get_model(body.critic_provider)

    # Wenn Critic = Generator (kein zweites Modell), anderen Stil nutzen
    same_provider = (body.generator_provider == body.critic_provider and
                     gen_model == crit_model)

    # Structure-Modell bestimmen (Qwen2.5 falls verfügbar)
    struct_model = body.structure_model or get_model(body.structure_provider)

    session = RefineSession(
        briefing=body.briefing,
        customer_name=body.customer_name,
        deck_size=body.deck_size,
        generator_provider=body.generator_provider,
        generator_model=gen_model,
        critic_provider=body.critic_provider,
        critic_model=crit_model,
        quality_threshold=body.quality_threshold,
        max_iterations=body.max_iterations,
    )
    # Struktur-Modell als Attribute setzen (für Agenda-Generierung)
    session.structure_provider = body.structure_provider
    session.structure_model = struct_model

    # Session initial speichern
    _save_session(session.session_id, session.to_dict())

    # Hintergrund-Thread
    def _run():
        all_events = []
        for event in refine_deck(session):
            all_events.append(event)
            # Session regelmäßig aktualisieren
            if event.get("type") in ("iteration_done", "slide_improve",
                                      "quality_reached", "done"):
                _save_session(session.session_id, {
                    **session.to_dict(),
                    "events": all_events,
                })
        # Finale Speicherung
        _save_session(session.session_id, {
            **session.to_dict(),
            "events": all_events,
        })

    t = threading.Thread(target=_run, daemon=True,
                         name=f"refiner-{session.session_id}")
    _running[session.session_id] = t
    t.start()

    return JSONResponse({
        "ok": True,
        "session_id": session.session_id,
        "generator":  f"{body.generator_provider}/{gen_model}",
        "critic":     f"{body.critic_provider}/{crit_model}",
        "structure":  f"{body.structure_provider}/{struct_model}",
        "same_provider": same_provider,
        "deck_size": body.deck_size,
        "quality_threshold": body.quality_threshold,
        "max_iterations": body.max_iterations,
        "stream_url": f"/refine/deck/{session.session_id}/stream",
        "note": (
            "Gleicher Provider für Generator und Critic" if same_provider else
            "Zwei verschiedene LLMs für maximale Qualität"
        ),
    })


@router.get("/deck/{session_id}/stream")
def stream_refine(session_id: str):
    """
    SSE-Stream: Live-Fortschritt des Refinement-Prozesses.

    Event-Typen:
      started        → Prozess gestartet
      agenda         → Deck-Struktur generiert
      slide_gen      → Slide initial erstellt
      slide_critique → Slide bewertet (mit Score)
      slide_improve  → Slide verbessert
      iteration_done → Iteration abgeschlossen
      quality_reached → Qualitätsziel erreicht
      done           → Fertig (enthält alle finalen Slides)
    """
    import time as _time

    def _sse():
        # Prüfen ob Session existiert oder noch läuft
        if session_id in _running and _running[session_id].is_alive():
            # Live: Events aus gespeicherter Session pollen
            seen = 0
            while True:
                data = _load_session(session_id)
                if data:
                    events = data.get("events", [])
                    for event in events[seen:]:
                        yield f"data: {json.dumps(event)}\n\n"
                        seen += 1
                    if data.get("status") == "done":
                        break
                _time.sleep(0.5)
        else:
            # Session bereits beendet oder nicht gefunden
            data = _load_session(session_id)
            if not data:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Session nicht gefunden'})}\n\n"
                return
            events = data.get("events", [])
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
                _time.sleep(0.01)  # Minimal Delay für Browser-Rendering

    return StreamingResponse(_sse(), media_type="text/event-stream")


@router.get("/deck/{session_id}")
def get_refine_result(session_id: str):
    """Ergebnis einer abgeschlossenen Refinement-Session."""
    data = _load_session(session_id)
    if not data:
        raise HTTPException(status_code=404,
                            detail=f"Session {session_id} nicht gefunden")

    # Events nicht in der Übersicht zurückgeben
    result = {k: v for k, v in data.items() if k != "events"}
    return JSONResponse({"ok": True, **result})


@router.post("/deck/{session_id}/export")
def export_refined_deck(session_id: str):
    """
    Exportiert ein verfeinertes Deck als PPTX.
    Nutzt die finalen (verbesserten) Slides der Session.
    """
    data = _load_session(session_id)
    if not data:
        raise HTTPException(status_code=404,
                            detail=f"Session {session_id} nicht gefunden")

    if data.get("status") != "done":
        raise HTTPException(status_code=409,
                            detail=f"Session noch nicht abgeschlossen (status: {data.get('status')})")

    slides = data.get("slides", [])
    if not slides:
        raise HTTPException(status_code=400, detail="Keine Slides vorhanden")

    try:
        from services.pptx_designer_v2 import PPTXDesignerV2
        import time as _time

        designer = PPTXDesignerV2()
        pptx_slides = [
            {
                "title": s["title"],
                "bullets": s.get("bullets", []),
                "type": s.get("slide_type", "content"),
                "notes": s.get("notes", ""),
                "sources": [],
            }
            for s in slides
        ]

        customer = data.get("customer_name") or "StratGen"
        output_path = designer.create_presentation(
            slides=pptx_slides,
            customer_name=customer,
            use_images=False,
        )

        return JSONResponse({
            "ok": True,
            "session_id": session_id,
            "output_path": str(output_path),
            "slide_count": len(slides),
            "avg_score": data.get("avg_score", 0),
            "download_url": f"/files/download?path={output_path}",
        })

    except Exception as e:
        log.error("Export failed for session %s: %s", session_id, e)
        raise HTTPException(status_code=500, detail=str(e))
