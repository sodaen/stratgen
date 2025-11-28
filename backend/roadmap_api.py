# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

class RoadmapReq(BaseModel):
    horizon_weeks: int = 16

@router.post("/suggest")
def roadmap_suggest(req: RoadmapReq = Body(...)):
    phases = [
        {"phase": "Discovery", "weeks": 2, "milestones": ["Brief final", "Hypothesen"]},
        {"phase": "Planung", "weeks": 2, "milestones": ["Budget/Mix", "KPI-Plan"]},
        {"phase": "Build", "weeks": 6, "milestones": ["Assets", "Setup", "QA"]},
        {"phase": "Run & Learn", "weeks": max(1, req.horizon_weeks - 10), "milestones": ["Go-Live", "Iterationen"]},
    ]
    return {"ok": True, "phases": phases}
