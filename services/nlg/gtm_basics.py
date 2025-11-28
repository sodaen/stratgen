# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register, bullets_safe

@register("gtm_basics")
def gtm_basics(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    topic = (project or {}).get("topic") or "Initiative"
    segs  = ((project or {}).get("facts") or {}).get("segments") or []
    out = {
        "title": "Executive Summary",
        "bullets": bullets_safe([
            f"Ziel: {topic} tragfähig am Markt verankern",
            "Kernzielgruppen klar priorisieren (Size × Fit × Reach)",
            "Wertversprechen + RTBs prägnant formulieren",
            "Kanalmix entlang des Funnels mit klaren Verantwortlichkeiten",
            "KPIs & Review-Rhythmus definieren"
        ]),
        "notes": ("Segmente: " + ", ".join(str(s) for s in segs)) if segs else ""
    }
    return out
