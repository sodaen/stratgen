# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register, bullets_safe

@register("market_sizing")
def market_sizing(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    topic = (project or {}).get("topic") or "Initiative"
    bullets = [
        "TAM/SAM/SOM grob abschätzen (Annahmen explizit nennen)",
        "Prior-Segmente: Größe × Fit × Erreichbarkeit",
        "Wachstumstreiber & saisonale Effekte",
        "Preisbereitschaft & Kaufmotive – Hypothesen",
        "Datenlücken & Validierungsplan (Research/Tests)"
    ]
    return {"title": f"Market Sizing ({topic})", "bullets": bullets, "notes":"Top-Down + Bottom-Up kombinieren; Quellen vermerken."}
