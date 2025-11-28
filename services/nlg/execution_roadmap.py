# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("execution_roadmap")
def execution_roadmap(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Milestones Q1–Q4 (Kampagnen/Assets/Enablement)",
        "Abhängigkeiten & kritische Pfade",
        "Rollen/Verantwortlichkeiten (RACI)",
        "Tooling/Stack (Tracking, Ads, CRM)",
        "Review-Rhythmus & Learnings-Loop"
    ]
    return {"title": "Roadmap & Meilensteine", "bullets": bullets, "notes":"Später Gantt/Owner/ETA ergänzen."}
