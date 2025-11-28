# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("value_proof")
def value_proof(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Top-3 Use Cases mit messbarem Outcome",
        "Mini-Case: Ausgangslage → Maßnahme → KPI-Effekt",
        "Beweise/RTBs: Zertifikate, Benchmarks, Kundenstimmen",
        "Proof Assets: Demos, Trials, Calculators",
        "Sozialer Beweis: Logos, Referenzen, Ratings"
    ]
    return {"title": "Value Proof / RTBs", "bullets": bullets, "notes":"Später echte Cases/Quellen substituieren."}
