# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register, bullets_safe

@register("competitive")
def competitive(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Wettbewerbs-Map: Direct vs. Alternative Solutions",
        "Feature-/Value-Gaps & Differenzierung",
        "Go-to-Market-Taktiken der Mitbewerber",
        "Preis/Packaging & Promotions",
        "Verteidigungs-/Angriffspunkte (Messaging/Channels)"
    ]
    return {"title": "Wettbewerb & Differenzierung", "bullets": bullets, "notes":"Mit echten Screens/Anzeigen ergänzen, wenn vorhanden."}
