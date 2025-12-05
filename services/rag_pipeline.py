# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, urllib.request, urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

API_BASE = os.environ.get("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")

def _jget(path: str, timeout: int = 10) -> Optional[Dict[str,Any]]:
    try:
        with urllib.request.urlopen(API_BASE + path, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def _read_snippet(p: str, max_chars: int = 220) -> str:
    try:
        with open(p, "r", encoding="utf-8") as f:
            s = f.read()
        s = " ".join([ln.strip() for ln in s.splitlines() if ln.strip()])
        return s[:max_chars]
    except Exception:
        return ""

def _collect_query(project: Dict[str,Any]) -> str:
    parts: List[str] = []
    if project.get("customer_name"): parts.append(str(project["customer_name"]))
    if project.get("topic"): parts.append(str(project["topic"]))
    outline = (project.get("outline") or {})
    if isinstance(outline, dict):
        for sec in (outline.get("sections") or [])[:6]:
            t = (sec or {}).get("title")
            if t: parts.append(str(t))
    return " ".join(parts).strip()

def _search_semantic(q: str, k: int) -> List[Dict[str,Any]]:
    try:
        qs = urllib.parse.urlencode({"q": q, "k": k})
        res = _jget(f"/knowledge/search_semantic?{qs}") or {}
        items = res.get("results") or res.get("items") or []
        out = []
        for it in items:
            p = it.get("path") or it.get("file") or ""
            if p:
                out.append({"path": p, "title": it.get("title") or Path(p).stem})
        return out[:max(1, int(k))]
    except Exception:
        return []

def build_facts(project: Dict[str,Any], k: int = 6) -> Dict[str,Any]:
    q = _collect_query(project)
    hits = _search_semantic(q, max(1, int(k or 6)))
    paths = [h["path"] for h in hits]
    bullets = [f"{Path(p).stem} — {_read_snippet(p)}" for p in paths]
    return {"k": int(k or 6), "hits": paths, "bullets": bullets, "sources": paths}

# ---- Stubs to satisfy optional imports elsewhere ----
COLL = "knowledge_base"

# Singleton für Qdrant Client
_qdrant_client = None
def get_qdrant():
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(host="localhost", port=6333)
        except Exception as e:
            print(f"Qdrant connection failed: {e}")
            return None
    return _qdrant_client

# Singleton für Embedder
_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Embedder init failed: {e}")
            return None
    return _embedder

def check_qdrant() -> Dict[str,Any]:
    try:
        qdr = get_qdrant()
        if qdr is None:
            return {"ok": False, "reason": "client is None"}
        collections = qdr.get_collections()
        return {"ok": True, "collections": [c.name for c in collections.collections]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_ollama() -> Dict[str,Any]:
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            return {"ok": True, "models": r.json().get("models", [])}
        return {"ok": False, "reason": f"status {r.status_code}"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
def generate_bullets_for(text: str, k: int = 5) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[:max(1, int(k or 5))]


# --- compat shims (appended, idempotent) ---
def _cosine_rerank(items, query_vec=None, top_k=None):
    lst=list(items or [])
    return lst[:int(top_k)] if top_k else lst

def _hybrid_rerank(items, query_vec=None, alpha: float=0.5, top_k=None):
    lst=list(items or [])
    return lst[:int(top_k)] if top_k else lst
