# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("go_no_go")
def go_no_go(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Go-Kriterien (z.B. ≥X qualifizierte Leads/Woche, CAC < Ziel)",
        "No-Go-Trigger (z.B. ROAS < Schwelle über 2 Wochen)",
        "Trial-/Pilot-Definition & Abbruchregeln",
        "Entscheidungs-Rhythmus (Weekly/Monthly)",
        "Owner für Go/No-Go-Entscheid"
    ]
    return {"title": "Go/No-Go-Kriterien", "bullets": bullets, "notes":"Entscheidungen dokumentieren (Changelog)."}
