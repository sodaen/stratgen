# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("channel_mix")
def channel_mix(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Base-Mix: Paid (SEA/Social/Video), Owned (Web/Email), Earned (PR)",
        "Kanäle entlang Funnel zuordnen (TOFU/MOFU/BOFU)",
        "Budget-Heuristik (z.B. 60/30/10) & Test-Budget",
        "Kreativ-Formate pro Kanal & Frequenzen",
        "Attribution/Measurement: UTM/Events/Cohorts"
    ]
    return {"title": "Channel Mix & Budget-Heuristik", "bullets": bullets, "notes":"Annahmen klar markieren; Tests einplanen."}
