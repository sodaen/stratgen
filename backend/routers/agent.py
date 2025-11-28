from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os, json, time

router = APIRouter(tags=["agent"])

CONFIG_DIR = os.path.join("data", "config")
PREFS_PATH = os.path.join(CONFIG_DIR, "agent_prefs.json")

def _load_prefs() -> Dict[str, Any]:
    try:
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_prefs(prefs: Dict[str, Any]) -> str:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = PREFS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PREFS_PATH)
    return PREFS_PATH

def _search_citations(query: str, k: int) -> List[Dict[str, Any]]:
    # Erst v2 nutzen, falls vorhanden
    try:
        from backend.routers.knowledge_search_v2 import SearchReq, search_semantic_v2
        res = search_semantic_v2(SearchReq(q=query, k=max(1, int(k)), dedup=True))  # type: ignore
        if isinstance(res, dict):
            return res.get("results", []) or []
    except Exception:
        pass
    # Fallback: alte knowledge_api
    try:
        from backend.knowledge_api import knowledge_search_semantic
        res = knowledge_search_semantic(q=query, k=max(1, int(k)))  # type: ignore
        if isinstance(res, dict):
            return res.get("results", []) or []
    except Exception:
        pass
    return []

class GenerateReq(BaseModel):
    prompt: Optional[str] = Field(default=None, description="Freitext-Prompt")
    project_id: Optional[str] = None
    topic: Optional[str] = None
    k: int = 6

@router.post("/agent/generate", operation_id="agent_generate")
def agent_generate(req: GenerateReq):
    query = (req.topic or req.prompt or (f"project {req.project_id}" if req.project_id else "")).strip() or "strategy preview"
    citations = _search_citations(query, req.k)
    outline = {
        "title": (req.topic or "Auto-Preview").strip() or "Auto-Preview",
        "sections": [
            {"title": "Einleitung", "bullets": ["Zielsetzung", "Kontext"]},
            {"title": "Kernpunkte", "bullets": ["These A", "These B", "These C"]},
        ],
    }
    diagnostics = {
        "ts": time.time(),
        "query": query,
        "citations_count": len(citations),
        "retrieval_k": req.k,
    }
    return {"outline": outline, "bullets": None, "citations": citations, "diagnostics": diagnostics}

class ReviewReq(BaseModel):
    content: str
    rules: Optional[List[str]] = Field(default=None, description="Optionale Regel-IDs (z. B. ['min_headings','max_sentence_len'])")

@router.post("/agent/review", operation_id="agent_review")
def agent_review(req: ReviewReq):
    text = req.content or ""
    issues: List[Dict[str, Any]] = []

    if text.count("#") < 1 and len(text) > 200:
        issues.append({"severity":"warn","rule":"min_headings","msg":"Mindestens eine Überschrift (# …) empfehlen."})
    if len(text.split()) < 50:
        issues.append({"severity":"info","rule":"too_short","msg":"Text ist sehr kurz; ggf. mehr Substanz ergänzen."})
    max_len = 160
    long_lines = [ln for ln in text.splitlines() if len(ln) > max_len]
    if long_lines:
        issues.append({"severity":"info","rule":"line_wrap","msg":f"{len(long_lines)} Zeile(n) >{max_len} Zeichen; Lesbarkeit verbessern."})

    return {"ok": True, "issues": issues, "stats": {"chars": len(text), "words": len(text.split())}}

class AutotuneReq(BaseModel):
    retrieval_k: Optional[int] = Field(default=None, ge=1, le=50)
    dedup: Optional[bool] = None
    rerank: Optional[bool] = None
    extra: Optional[Dict[str, Any]] = None

@router.post("/agent/autotune", operation_id="agent_autotune")
def agent_autotune(req: AutotuneReq):
    prefs = _load_prefs()
    for k, v in req.dict(exclude_none=True).items():
        prefs[k] = v
    saved_to = _save_prefs(prefs)
    return {"ok": True, "saved_to": saved_to, "prefs": prefs}

@router.get("/agent/health", operation_id="agent_health")
def agent_health():
    return {"ok": True, "component": "agent"}
