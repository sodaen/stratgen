from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
import requests, os

router = APIRouter()

def _api(path: str) -> str:
    base = os.environ.get("STRATGEN_BASE", "http://127.0.0.1:8011")
    return f"{base}{path}"

def _post(path: str, json: Dict[str, Any] | None = None):
    return requests.post(_api(path), json=json or {}, timeout=120)

@router.post("/agent/generate_v2")
def agent_generate_v2(body: Dict[str, Any] | None = None):
    body = body or {}
    topic  = body.get("topic") or body.get("title") or body.get("prompt") or "Web Run"
    slides = int(body.get("slides") or 100)

    # 1) Projekt anlegen
    r = _post("/projects/save", {"customer_name":"Web", "topic": topic})
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"save failed: {r.text}")
    pid = r.json().get("project",{}).get("id")
    if not pid:
        raise HTTPException(500, "no project id")

    # 2) v1 Generate – großer Plan
    modules = ["gtm_basics","personas","market_sizing","competitive","value_proof",
               "channel_mix","funnel","kpis","execution_roadmap","risks_mitigations",
               "guardrails","go_no_go"]
    r2 = _post(f"/projects/{pid}/generate", {"modules": modules, "slides": slides})
    if r2.status_code != 200:
        raise HTTPException(r2.status_code, f"generate failed: {r2.text}")

    # Semantik wie v2: gib project_id zurück
    return {"ok": True, "project_id": pid}

@router.post("/exports/make_v2")
def exports_make_v2(body: Dict[str, Any] | None = None):
    body = body or {}
    pid = body.get("project_id")
    if not pid:
        raise HTTPException(400, "project_id required")

    # Enrich (LLM+RAG, lang)
    _post(f"/projects/{pid}/enrich", {"length":"long","use_llm":True,"rag":{"enabled":True}})

    # Critique
    _post(f"/projects/{pid}/critique", {})

    # Autotune ×2
    _post(f"/projects/{pid}/autotune", {})
    _post(f"/projects/{pid}/autotune", {})

    # Rendern
    r = _post(f"/pptx/render_from_project/{pid}", {"slides": None})
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"render failed: {r.text}")
    out = r.json()
    name = (out.get("path","").split("/")[-1]) if out.get("path") else None
    return {"name": name, "url": out.get("url"), "size": None, "mtime": None, "checksum": None}
