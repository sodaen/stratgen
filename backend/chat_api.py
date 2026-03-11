# -*- coding: utf-8 -*-
"""
StratGen – Interactive Chat API (Sprint 3)
Multi-Turn Chat mit RAG-Kontext, Session-gebunden, Streaming.

Endpoints:
  POST /chat/{session_id}/message   – Nachricht senden, Antwort + RAG
  GET  /chat/{session_id}/history   – Gesprächsverlauf
  DELETE /chat/{session_id}         – Session löschen
  POST /chat/{session_id}/feedback  – Thumbs up/down auf letzte Antwort
  GET  /chat/sessions               – Alle Chat-Sessions
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

log = logging.getLogger("stratgen.chat")

router = APIRouter(prefix="/chat", tags=["chat"])

CHAT_DIR = Path("data/chats")
CHAT_DIR.mkdir(parents=True, exist_ok=True)

MAX_HISTORY = 20      # Nachrichten im Kontext-Fenster
MAX_CONTEXT_CHARS = 3000  # RAG-Kontext zeichenlimit


# ─────────────────────────────────────────────
# LLM + RAG HELPERS
# ─────────────────────────────────────────────

def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def _model() -> str:
    return os.getenv("LLM_MODEL", "mistral")

def _llm(prompt: str, max_tokens: int = 1200) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        try:
            r = requests.post(
                f"{_ollama_host()}/api/generate",
                json={"model": _model(), "prompt": prompt, "stream": False,
                      "options": {"num_predict": max_tokens, "temperature": 0.7}},
                timeout=120,
            )
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception as e:
            log.warning("LLM call failed: %s", e)
            return ""
    if provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            log.warning("OpenAI call failed: %s", e)
            return ""
    return ""


def _llm_stream(prompt: str, max_tokens: int = 1200):
    """Generator für Streaming-Response von Ollama."""
    try:
        r = requests.post(
            f"{_ollama_host()}/api/generate",
            json={"model": _model(), "prompt": prompt, "stream": True,
                  "options": {"num_predict": max_tokens, "temperature": 0.7}},
            timeout=120,
            stream=True,
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
                except Exception:
                    continue
    except Exception as e:
        log.warning("LLM stream failed: %s", e)
        yield ""


def _rag_search(query: str, session_id: str = "", k: int = 5) -> List[Dict]:
    """RAG-Suche in Knowledge Base + optionaler Session-Collection."""
    results = []
    base = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")

    # Haupt-KB
    try:
        r = requests.get(
            f"{base}/knowledge/search_semantic",
            params={"q": query, "k": k},
            timeout=15,
        )
        if r.ok:
            hits = r.json().get("_hits") or r.json().get("results") or []
            for h in hits[:k]:
                txt = h.get("snippet") or h.get("text") or ""
                src = h.get("path") or h.get("source") or ""
                if txt:
                    results.append({"text": txt[:600], "source": src, "score": h.get("score", 0)})
    except Exception as e:
        log.debug("RAG search failed: %s", e)

    # Session-spezifische Collection
    if session_id:
        try:
            r2 = requests.get(
                f"{base}/learning/session/{session_id}/search",
                params={"query": query, "limit": 3},
                timeout=10,
            )
            if r2.ok:
                for hit in (r2.json().get("results") or []):
                    txt = hit.get("text", "")
                    if txt:
                        results.append({"text": txt[:400], "source": "session", "score": hit.get("score", 0)})
        except Exception:
            pass

    # Nach Score sortieren
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:k]


def _build_prompt(
    user_message: str,
    history: List[Dict],
    rag_results: List[Dict],
    system_context: str = "",
    lang: str = "de",
) -> str:
    """Baut den vollständigen Prompt für den LLM."""
    lang_instr = "Antworte auf Deutsch, präzise und hilfreich." if lang == "de" else "Answer in English, precisely and helpfully."

    # RAG-Kontext
    rag_block = ""
    if rag_results:
        snippets = []
        total = 0
        for r in rag_results:
            txt = r["text"]
            if total + len(txt) > MAX_CONTEXT_CHARS:
                break
            src = r.get("source", "")
            snippets.append(f"[{src}]: {txt}")
            total += len(txt)
        rag_block = "\n\nRelevante Informationen aus der Wissensdatenbank:\n" + "\n\n".join(snippets)

    # Gesprächshistorie (letzte N Nachrichten)
    history_block = ""
    recent = history[-(MAX_HISTORY * 2):]  # user+assistant pairs
    if recent:
        turns = []
        for msg in recent:
            role = "Nutzer" if msg["role"] == "user" else "Assistent"
            turns.append(f"{role}: {msg['content']}")
        history_block = "\n\nBisheriges Gespräch:\n" + "\n".join(turns)

    system = system_context or (
        "Du bist ein intelligenter Strategie-Assistent für StratGen. "
        "Du hilfst bei der Erstellung von Präsentationen, Strategien und Analysen. "
        "Nutze den Kontext aus der Wissensdatenbank wenn relevant. "
        "Sei präzise, konkret und handlungsorientiert."
    )

    prompt = f"""{system}

{lang_instr}{rag_block}{history_block}

Nutzer: {user_message}

Assistent:"""

    return prompt


# ─────────────────────────────────────────────
# CHAT SESSION MANAGEMENT
# ─────────────────────────────────────────────

def _load_session(session_id: str) -> Optional[Dict]:
    f = CHAT_DIR / f"{session_id}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_session(session_id: str, data: Dict):
    f = CHAT_DIR / f"{session_id}.json"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _new_session(session_id: str, **kwargs) -> Dict:
    data = {
        "id": session_id,
        "created_at": time.time(),
        "updated_at": time.time(),
        "history": [],
        "context": {},
        **kwargs,
    }
    _save_session(session_id, data)
    return data


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str
    use_rag: bool = True
    stream: bool = False
    lang: str = "de"
    context: Optional[Dict[str, Any]] = None  # z.B. {"project_name": "X", "company": "Y"}


class FeedbackMsg(BaseModel):
    message_id: str
    rating: str  # positive|negative|neutral
    correction: Optional[str] = None


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/{session_id}/message")
def send_message(session_id: str, body: ChatMessage):
    """
    Sendet eine Nachricht und bekommt eine LLM+RAG-Antwort.
    Speichert den Verlauf persistent pro Session.
    """
    session = _load_session(session_id) or _new_session(session_id)

    # Kontext updaten
    if body.context:
        session["context"].update(body.context)

    # RAG-Suche
    rag_results = []
    rag_sources = []
    if body.use_rag:
        rag_results = _rag_search(body.message, session_id)
        rag_sources = [r.get("source", "") for r in rag_results if r.get("source")]

    # System-Kontext aus Session
    ctx = session.get("context", {})
    system_ctx = ""
    if ctx.get("project_name") or ctx.get("company"):
        system_ctx = (
            f"Du arbeitest an einem Projekt für {ctx.get('company', 'den Kunden')}. "
            f"Projekt: {ctx.get('project_name', '')}. "
            f"Branche: {ctx.get('industry', '')}. "
            "Nutze diesen Kontext in deinen Antworten."
        )

    # Prompt bauen
    prompt = _build_prompt(
        user_message=body.message,
        history=session["history"],
        rag_results=rag_results,
        system_context=system_ctx,
        lang=body.lang,
    )

    # LLM aufrufen
    answer = _llm(prompt)

    if not answer:
        answer = (
            "LLM nicht verfügbar. Bitte Ollama starten: `ollama run mistral`\n"
            "Oder LLM_PROVIDER / OPENAI_API_KEY konfigurieren."
        )

    # Message-ID für Feedback-Tracking
    msg_id = str(uuid.uuid4())

    # History updaten
    session["history"].append({"role": "user", "content": body.message, "timestamp": time.time()})
    session["history"].append({
        "role": "assistant",
        "content": answer,
        "id": msg_id,
        "sources": rag_sources,
        "rag_hits": len(rag_results),
        "timestamp": time.time(),
    })
    session["updated_at"] = time.time()

    # Persistieren (History auf MAX_HISTORY kürzen)
    if len(session["history"]) > MAX_HISTORY * 2:
        session["history"] = session["history"][-(MAX_HISTORY * 2):]

    _save_session(session_id, session)

    # Feedback-Logging (async, non-blocking)
    try:
        from services.chat_learner import save_chat_feedback
        save_chat_feedback(
            query=body.message,
            answer=answer,
            sources=rag_sources,
            rating="neutral",
        )
    except Exception:
        pass

    return {
        "ok": True,
        "message_id": msg_id,
        "answer": answer,
        "sources": rag_sources,
        "rag_hits": len(rag_results),
        "model": _model(),
        "session_id": session_id,
    }


@router.post("/{session_id}/message/stream")
def send_message_stream(session_id: str, body: ChatMessage):
    """Streaming-Version des Chat-Endpoints (Server-Sent Events)."""
    session = _load_session(session_id) or _new_session(session_id)

    if body.context:
        session["context"].update(body.context)

    rag_results = []
    if body.use_rag:
        rag_results = _rag_search(body.message, session_id)

    ctx = session.get("context", {})
    system_ctx = ""
    if ctx.get("company"):
        system_ctx = f"Kontext: Unternehmen={ctx.get('company')}, Projekt={ctx.get('project_name','')}"

    prompt = _build_prompt(
        user_message=body.message,
        history=session["history"],
        rag_results=rag_results,
        system_context=system_ctx,
        lang=body.lang,
    )

    collected = []

    def generate():
        for token in _llm_stream(prompt):
            collected.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Nach Stream: History speichern
        answer = "".join(collected)
        msg_id = str(uuid.uuid4())
        session["history"].append({"role": "user", "content": body.message, "timestamp": time.time()})
        session["history"].append({
            "role": "assistant", "content": answer, "id": msg_id,
            "rag_hits": len(rag_results), "timestamp": time.time(),
        })
        session["updated_at"] = time.time()
        if len(session["history"]) > MAX_HISTORY * 2:
            session["history"] = session["history"][-(MAX_HISTORY * 2):]
        _save_session(session_id, session)

        yield f"data: {json.dumps({'done': True, 'message_id': msg_id})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{session_id}/history")
def get_history(session_id: str, limit: int = 50):
    """Gibt den Gesprächsverlauf zurück."""
    session = _load_session(session_id)
    if not session:
        return {"ok": True, "history": [], "session_id": session_id}
    history = session.get("history", [])
    return {
        "ok": True,
        "session_id": session_id,
        "history": history[-limit:],
        "total_messages": len(history),
        "context": session.get("context", {}),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
    }


@router.post("/{session_id}/feedback")
def submit_feedback(session_id: str, body: FeedbackMsg):
    """Thumbs up/down auf eine Antwort — triggert Self-Learning."""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(404, "Session nicht gefunden")

    # Nachricht in History finden und markieren
    for msg in session.get("history", []):
        if msg.get("id") == body.message_id:
            msg["feedback"] = body.rating
            msg["correction"] = body.correction
            break

    _save_session(session_id, session)

    # Chat-Learner informieren
    try:
        from services.chat_learner import save_chat_feedback
        # Finde user-Nachricht die davor kam
        history = session.get("history", [])
        for i, msg in enumerate(history):
            if msg.get("id") == body.message_id and i > 0:
                user_msg = history[i - 1].get("content", "")
                save_chat_feedback(
                    query=user_msg,
                    answer=msg.get("content", ""),
                    sources=msg.get("sources", []),
                    rating=body.rating,
                    user_correction=body.correction,
                )
                break
    except Exception as e:
        log.debug("Chat feedback save failed: %s", e)

    # Self-Learning Score updaten
    if body.message_id:
        try:
            from services.self_learning import self_learning
            score = 5 if body.rating == "positive" else (1 if body.rating == "negative" else 3)
            self_learning.record_feedback(body.message_id, score, session_id)
        except Exception:
            pass

    return {"ok": True, "message_id": body.message_id, "rating": body.rating}


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Löscht eine Chat-Session."""
    f = CHAT_DIR / f"{session_id}.json"
    if f.exists():
        f.unlink()
    return {"ok": True}


@router.get("/sessions")
def list_sessions(limit: int = 20):
    """Listet alle Chat-Sessions."""
    sessions = []
    for f in sorted(CHAT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": data.get("id", f.stem),
                "message_count": len(data.get("history", [])),
                "context": data.get("context", {}),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
            })
        except Exception:
            continue
    return {"ok": True, "sessions": sessions, "count": len(sessions)}


@router.post("/sessions/new")
def create_session(
    company: Optional[str] = None,
    project_name: Optional[str] = None,
    industry: Optional[str] = None,
):
    """Erstellt eine neue Chat-Session und gibt die ID zurück."""
    session_id = str(uuid.uuid4())
    _new_session(
        session_id,
        context={
            "company": company or "",
            "project_name": project_name or "",
            "industry": industry or "",
        },
    )
    return {"ok": True, "session_id": session_id}
