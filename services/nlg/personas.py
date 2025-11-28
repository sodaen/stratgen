# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register, bullets_safe

@register("personas")
def personas(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    segs = ((project or {}).get("facts") or {}).get("segments") or ["Primär", "Sekundär"]
    bullets = []
    for s in segs[:2]:
        bullets.append(f"Segment: {s} – Needs/Jobs, Pain/Gain, Entscheiderlogik")
    bullets.append("Entscheider-/Influencer-Rollen & Einwände mappen")
    return {
        "title": "Zielgruppen & Bedürfnisse",
        "bullets": bullets,
        "notes": "Basis für Positionierung, Content & Kanäle"
    }
