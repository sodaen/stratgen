# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, Optional, List
import time

router = APIRouter(prefix="/projects", tags=["projects"])

# sehr einfacher In-Memory-Store (für E2E ausreichend)
_PROJECTS: Dict[str, Dict[str, Any]] = {}

def _now() -> int:
    return int(time.time())

def _ensure_project_id(p: Dict[str, Any]) -> str:
    pid = (p.get("id") or p.get("project_id") or "").strip()
    if not pid:
        pid = f"proj-{_now()}"
        p["id"] = pid
    return pid

def _merge_meta_k(project: Dict[str, Any], body: Optional[Dict[str, Any]]):
    """Nur k in project.meta übernehmen – NICHT an generate() übergeben."""
    try:
        if body and "k" in body:
            k = int(body.get("k"))
            meta = project.setdefault("meta", {})
            meta["k"] = k
    except Exception:
        pass

@router.post("/save")
def save_project(payload: Dict[str, Any] = Body(...)):
    """Minimal speichern & in In-Memory-Store persistieren."""
    project = {
        "id": None,
        "customer_name": payload.get("customer_name"),
        "topic": payload.get("topic"),
        "outline": payload.get("outline") or {},
        "meta": payload.get("meta") or {},
        "style": payload.get("style"),
        "facts": payload.get("facts") or {},
        "logo": payload.get("logo"),
        "created_at": _now(),
        "updated_at": _now(),
    }
    pid = _ensure_project_id(project)
    _PROJECTS[pid] = project
    return {"ok": True, "project": project, "created": True}

@router.get("/{pid}")
def get_project(pid: str):
    """GET für PPTX/Diagnostics – muss immer vorhanden sein."""
    pr = _PROJECTS.get(str(pid))
    if not pr:
        raise HTTPException(status_code=404, detail="project not found")
    pr.setdefault("id", str(pid))
    return {"ok": True, "project": pr}

def _call_generator(project: Dict[str, Any], slides: Optional[int], modules: Optional[List[Dict[str, Any]]]):
    """Robuste Delegation an services.generator.generate(project, slides=..., modules=...)"""
    try:
        from services.generator import generate  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"generator not available: {e}")

    want = 10 if slides is None else int(slides)
    mods = modules if isinstance(modules, list) and modules else None
    try:
        out = generate(project, slides=want, modules=mods)   # bevorzugte Signatur
    except TypeError:
        out = generate(project=project, slides=want, modules=mods)  # Fallback
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"generate failed: {e}")

    out = out or {}
    updated = out.get("project") or project
    try:
        updated["updated_at"] = _now()
    except Exception:
        pass
    return {"ok": True, "project": updated, "meta": out.get("meta") or updated.get("meta") or {}}

@router.post("/{pid}/generate")
def generate_project(pid: str, body: Optional[Dict[str, Any]] = Body(None)):
    pr = _PROJECTS.get(pid)
    if not pr:
        raise HTTPException(status_code=404, detail="project not found")
    _merge_meta_k(pr, body)
    slides = None
    modules = None
    if isinstance(body, dict):
        slides = body.get("slides")
        modules = body.get("modules")
    res = _call_generator(pr, slides=slides, modules=modules)
    _PROJECTS[pid] = res["project"]
    return {"ok": True, "project": res["project"], "created": False}

@router.post("/{id}/generate")
def generate_project_id(id: str, body: Optional[Dict[str, Any]] = Body(None)):
    # Alias – identisch zu /{pid}/generate
    return generate_project(id, body)
