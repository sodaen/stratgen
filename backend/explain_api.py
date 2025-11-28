# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Query
router = APIRouter(prefix="/explain", tags=["explain"])

@router.get("/why")
def explain_why(recommendation: str = Query(..., description="Empfehlung, die erklärt werden soll")):
    heuristics = [
        "Benchmarks aus ähnlichen Kunden/Industrien",
        "Kosten/Nutzen-Schätzung (CPL/CPA)",
        "Risiko-Assessment (Channel, Creative, Tracking)",
        "Roadmap-Abhängigkeiten (Zeit/Budget/Team)",
    ]
    return {"ok": True, "recommendation": recommendation, "based_on": heuristics}
