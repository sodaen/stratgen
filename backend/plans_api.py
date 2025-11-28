# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/plans", tags=["plans"])

class MixReq(BaseModel):
    budget_eur: float = 10000.0
    objective: str = "Leads"
    countries: list[str] = ["DE"]

@router.post("/media_mix")
def media_mix(req: MixReq = Body(...)):
    # naive split
    parts = {
        "Search": 0.35,
        "Paid Social": 0.35,
        "Display/Programmatic": 0.20,
        "Content/Production": 0.10,
    }
    allocation = {k: round(req.budget_eur * v, 2) for k, v in parts.items()}
    risks = ["Budget zu gering für Always-on", "Creative Wearout", "Tracking-Limits (Privacy)"]
    return {"ok": True, "allocation": allocation, "objective": req.objective, "countries": req.countries, "risks": risks}
