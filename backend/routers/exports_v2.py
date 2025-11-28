# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from typing import Any, Dict, List, Optional
import os, json, urllib.request, urllib.error, os.path as op

router = APIRouter(prefix="/exports", tags=["exports-v2"])
API = os.environ.get("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011")

DEFAULT_MODULES: List[str] = [
    "gtm_basics","personas","market_sizing","competitive","value_proof",
    "channel_mix","funnel","kpis","execution_roadmap","risks_mitigations",
    "guardrails","go_no_go"
]

def _post(path:str, payload:Dict[str,Any]|None=None, timeout:int=300) -> Dict[str,Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}

@router.post("/make_v2")
def make_v2(body: Dict[str, Any] = Body(default={})):
    # Falls die UI KEINE project_id übergibt, fahren wir die komplette Kette in EINEM Call.
    topic   = body.get("topic") or body.get("title") or "Untitled"
    org     = body.get("org")   or body.get("customer_name") or "Global"
    modules = body.get("modules") or DEFAULT_MODULES
    slides  = int(body.get("slides") or 50)
    k       = int(body.get("k") or 12)

    pid = body.get("project_id")
    if not pid:
        saved = _post("/projects/save", {"customer_name": org, "topic": topic})
        pid = saved["project"]["id"]
        _post(f"/projects/{pid}/generate", {"modules": modules, "slides": slides})

        try:
            _post("/knowledge/search_semantic_v2", {"query": topic, "k": k})
        except Exception:
            pass
        _post(f"/projects/{pid}/enrich",   {"length": "long", "use_llm": True})
        _post(f"/projects/{pid}/critique", {})
        try:
            _post(f"/projects/{pid}/autotune", {})
            _post(f"/projects/{pid}/autotune", {})
        except Exception:
            pass
    else:
        # project_id vorhanden → zur Sicherheit Heavy-Schritte trotzdem laufen lassen
        try:
            _post("/knowledge/search_semantic_v2", {"query": topic, "k": k})
        except Exception:
            pass
        _post(f"/projects/{pid}/enrich",   {"length": "long", "use_llm": True})
        _post(f"/projects/{pid}/critique", {})
        try:
            _post(f"/projects/{pid}/autotune", {})
            _post(f"/projects/{pid}/autotune", {})
        except Exception:
            pass

    out = _post(f"/pptx/render_from_project/{pid}", {})
    path = out.get("path") or out.get("file") or ""
    url  = out.get("url")  or (("/exports/download/" + op.basename(path)) if path else None)
    name = op.basename(path) if path else None

    return {"ok": True, "project_id": pid, "slides": slides, "path": path, "url": url, "name": name}
