# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/metrics", tags=["metrics"])

class MetricsReq(BaseModel):
    objective: str = "Leads"
    horizon_weeks: int = 12
    budget_eur: float | None = None

@router.post("/suggest")
def metrics_suggest(req: MetricsReq = Body(...)):
    plan = [
        {"kpi": "Leads", "target": 100, "measurement": "CRM (MQL)", "cadence": "wöchentlich"},
        {"kpi": "CTR", "target": 2.5, "measurement": "Ad-Plattform", "cadence": "wöchentlich"},
        {"kpi": "CPL", "target": 50, "measurement": "Spend/Leads", "cadence": "wöchentlich"},
        {"kpi": "Pipeline €", "target": 50000, "measurement": "CRM", "cadence": "monatlich"},
    ]
    return {"ok": True, "objective": req.objective, "horizon_weeks": req.horizon_weeks, "plan": plan}
