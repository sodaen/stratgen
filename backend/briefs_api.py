# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from backend.utils_projects import load_project, save_project

router = APIRouter(prefix="/briefs", tags=["briefs"])

class BriefSuggestReq(BaseModel):
    customer_name: Optional[str] = None
    topic: Optional[str] = None
    goals: List[str] = []
    constraints: List[str] = []

class BriefSuggestResp(BaseModel):
    ok: bool
    questions: List[str]
    brief: Dict[str, Any]

@router.post("/suggest", response_model=BriefSuggestResp)
def briefs_suggest(req: BriefSuggestReq):
    base_qs = [
        "Was ist das primäre Business-Ziel (1–2 Sätze)?",
        "Welche Zielgruppen priorisieren wir (Top 3)?",
        "Welche Kernbotschaft soll hängen bleiben?",
        "Welche Kanäle sind gesetzt / tabu?",
        "Welche KPIs messen Erfolg im Quartal 1?",
        "Welche Budget-Range ist realistisch?",
        "Welche Risiken/Constraints kennen wir bereits?",
        "Welche bestehenden Assets (Brand, Content, Daten) sind verfügbar?"
    ]
    qs = base_qs
    brief = {
        "customer_name": req.customer_name,
        "topic": req.topic,
        "goals": req.goals or [],
        "constraints": req.constraints or [],
        "kickoff_questions": qs,
    }
    return {"ok": True, "questions": qs, "brief": brief}

class MergeReq(BaseModel):
    brief: Dict[str, Any]

@router.post("/merge_to_project")
def briefs_merge_to_project(project_id: str = Query(...), body: MergeReq = Body(...)):
    pj = load_project(project_id)
    pj["brief"] = body.brief
    out = save_project(pj)
    if not out or not out.get("ok"):
        raise HTTPException(status_code=500, detail="save_project failed")
    return {"ok": True, "project_id": pj["id"]}
