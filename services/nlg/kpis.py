# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List
from . import register

@register("kpis")
def kpis(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    # einfache Defaults – wird durch spätere Enrichment-/Critique-Pässe verfeinert
    title = "KPIs & Zielwerte"
    bullets: List[str] = [
        "Pipeline (MQL/SQL): Zielwerte je Quartal definieren",
        "CAC / CLV: Verhältnis und Zielkorridore festlegen",
        "Conversion-Rates: Awareness → Consideration → Purchase",
        "Channel-KPIs: CTR, CPC/CPM, ROAS pro Kanal",
        "Sales-KPIs: Win-Rate, Sales-Cycle, Average Deal Size",
        "Reporting-Cadence & Verantwortlichkeiten"
    ]
    notes = "Basierend auf Markt, Budget und Funnel-Annahmen; später mit echten Benchmarks anreichern."
    return {"title": title, "bullets": bullets, "notes": notes}
