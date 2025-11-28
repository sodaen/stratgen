# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from backend.utils_projects import load_project, save_project
from backend.personas_api import personas_suggest, PersonasReq
from backend.messaging_api import messaging_matrix
from backend.metrics_api import metrics_suggest, MetricsReq
from backend.plans_api import media_mix, MixReq
from backend.critique_api import project_critique
from backend.versioning_api import snapshot

router = APIRouter(prefix="/projects", tags=["enrich"])

@router.post("/{project_id}/enrich")
def enrich_project(project_id: str):
    pj: Dict[str, Any] = load_project(project_id)
    brief: Dict[str, Any] = pj.get("brief") or {}
    goals = brief.get("goals") if isinstance(brief.get("goals"), list) else []
    objective = (goals[0] if goals else "Leads")

    # Personas
    try:
        pr = PersonasReq()  # nutzt Defaults (z.B. "DE")
        personas = personas_suggest(pr)["personas"]
        pj["personas"] = personas
    except Exception:
        pj["personas"] = []

    # Messaging (toleranter Body)
    try:
        body = {
            "personas": pj.get("personas") or [{"name": "Generic"}],
            "value_props": ["Effizient", "Nachweisbar", "Sicher"]
        }
        pj["messaging"] = messaging_matrix(body)["matrix"]
    except Exception:
        pj["messaging"] = []

    # Metrics
    try:
        pj["metrics_plan"] = metrics_suggest(MetricsReq(objective=objective, horizon_weeks=12))["plan"]
    except Exception:
        pj["metrics_plan"] = []

    # Media Mix
    try:
        pj["media_mix"] = media_mix(MixReq(budget_eur=15000.0, objective=objective, countries=["DE"]))["allocation"]
    except Exception:
        pj["media_mix"] = {}

    # Critique
    try:
        pj["critique"] = project_critique(project_id)
    except Exception:
        pj["critique"] = {}

    out = save_project(pj)
    if not (out and out.get("ok")):
        raise HTTPException(status_code=500, detail="save_project failed")

    # Version-Snapshot
    snapshot(project_id)
    return {"ok": True, "project_id": project_id}
