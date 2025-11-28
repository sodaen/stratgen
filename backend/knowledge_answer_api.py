
# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from typing import Any, Dict, List
import os, requests

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.get('/health', operation_id="knowledge_health_get")
def health_():
    import os
    return {'ok': True, 'use_llm': os.environ.get('USE_LLM_ENHANCE','0')=='1'}


BASE = os.environ.get("BASE", "http://127.0.0.1:8011")
OLLAMA = os.environ.get("OLLAMA_HOST", "").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "mistral")
USE_LLM = os.environ.get("USE_LLM_ENHANCE", "0") == "1"

def _to_sources(items: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    out: List[Dict[str,Any]] = []
    for it in (items or [])[:5]:
        pay = it.get("payload") or {}
        txt = pay.get("text") or pay.get("content") or it.get("text") or ""
        out.append({
            "score": it.get("score"),
            "text": (txt or "").strip(),
            "path": pay.get("path") or pay.get("source_path"),
            "type": pay.get("type") or pay.get("source_type") or "file",
            "title": pay.get("title"),
        })
    return out

def _llm_summarize(chunks: List[str], q: str) -> str:
    # Fallback auf Heuristik, wenn kein OLLAMA konfiguriert
    if not (USE_LLM and OLLAMA):
        return _heuristic_summarize(chunks)

    prompt = (
        "Verdichte die folgenden Auszüge streng faktenbasiert als Stichpunkte (max. 8), "
        "ohne neue Fakten zu erfinden. Beantworte die Frage nur mit Inhalten aus den Auszügen.\n\n"
        f"FRAGE: {q}\n\nAUSZUEGE:\n- " + "\n- ".join([c.strip() for c in chunks if c.strip()])
    )
    try:
        r = requests.post(
            f"{OLLAMA}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=30,
        )
        if r.status_code != 200:
            return _heuristic_summarize(chunks)
        js = r.json() or {}
        out = (js.get("response") or "").strip()
        return out or _heuristic_summarize(chunks)
    except Exception:
        return _heuristic_summarize(chunks)

def _heuristic_summarize(chunks: List[str]) -> str:
    # dedupe + hartes Kürzen
    seen, lines = set(), []
    for c in chunks:
        for ln in (c or "").splitlines():
            ln = ln.strip()
            if not ln: 
                continue
            if ln in seen:
                continue
            seen.add(ln)
            lines.append(ln)
            if len(lines) >= 8:
                break
        if len(lines) >= 8:
            break
    return "\n".join(lines) if lines else "Kein Knowledge-Treffer."

@router.post("/answer", operation_id="knowledge_answer_post")
def answer(body: Dict[str,Any] = Body(...)) -> Dict[str,Any]:
    try:
        q = (body or {}).get("q") or ""
        customer = (body or {}).get("customer") or ""
        limit = int((body or {}).get("limit") or 5)
        if not q:
            return {"ok": False, "error": "missing 'q'"}

        # 1) Qdrant/RAG abfragen
        r = requests.post(
            f"{BASE}/datasources/query",
            json={"customer_name": customer, "query": q, "limit": max(1, min(limit, 20))},
            timeout=20,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"/datasources/query {r.status_code}: {r.text}"}
        data = r.json() or {}
        items = data.get("items") or data.get("results") or []

        # 2) Texte einsammeln
        parts: List[str] = []
        for it in items[:max(1, min(limit, 5))]:
            pay = it.get("payload") or {}
            txt = pay.get("text") or pay.get("content") or it.get("text")
            if txt:
                parts.append(str(txt).strip())

        # 3) Antwort bauen (LLM oder Heuristik)
        answer_text = _llm_summarize(parts, q) if parts else "Kein Knowledge-Treffer."

        return {"ok": True, "answer": answer_text, "sources": _to_sources(items)}
    except Exception as e:
        # niemals None zurückgeben
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
