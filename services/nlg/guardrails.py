# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("guardrails")
def guardrails(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Brand-Guardrails (CI/CD, Claims, Tonalität)",
        "Rechtliches (Claims/Datenschutz/Branchenregeln)",
        "KPI-Minima (z.B. CTR/CVR/ROAS) und Stop-Loss",
        "Kreativ-Do/Don'ts & QA-Checklisten",
        "Escalation-Pfad & Freigaben"
    ]
    return {"title": "Guardrails & Governance", "bullets": bullets, "notes":"Checklisten verlinken; Owner benennen."}
