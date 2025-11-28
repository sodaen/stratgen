# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register, bullets_safe

@register("funnel")
def funnel(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "TOFU: Reichweite/Attention (Paid Social/Video, PR)",
        "MOFU: Education/Nurture (Web, SEO, Email, Webinar)",
        "BOFU: Conversion (SEA, Retargeting, Sales-Enablement)",
        "Owned-First: Website als Content-Hub"
    ]
    return {
        "title": "Kanalstrategie (Funnel)",
        "bullets": bullets,
        "notes": "Mit Journey, Creatives und Verantwortlichkeiten verknüpfen"
    }
