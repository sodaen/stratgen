# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Union
import json

# Versuche die echten Presets & den Shim zu laden
try:
    from services.style_presets import PRESETS, get_style_options  # type: ignore
except Exception:
    PRESETS = {}  # type: ignore
    def get_style_options(name: str) -> Dict[str, Any]:  # type: ignore
        return {}

# Welche Keys ein Style mindestens bereitstellen soll
REQUIRED_STYLE_KEYS = ("title_font","body_font","accent_color","text_color","bg_color")

# Letzte Rettung: ein funktionaler Minimal-Style falls alles andere versagt
DEFAULT_STYLE: Dict[str, Any] = {
    "title_font": "Calibri",
    "body_font": "Calibri",
    "accent_color": "2F5597",
    "text_color": "000000",
    "bg_color": "FFFFFF",
    "title_size": 40,
    "body_size": 20,
    "margin": 24,
}

def _has_required_keys(d: Dict[str, Any]) -> bool:
    return all(k in d for k in REQUIRED_STYLE_KEYS)

def ensure_outline_dict(data: Union[str, Dict[str, Any], None]) -> Dict[str, Any]:
    """
    Nimmt dict|str|None an und gibt immer ein Dict zurück.
    - dict → unverändert
    - str  → JSON decode (fehlschlägt: {})
    - None/sonstiges → {}
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}

def resolve_style(style_like: Union[str, Dict[str, Any], None]) -> Dict[str, Any]:
    """
    Vereinheitlicht Styles:
    - Dict passthrough
    - Name → get_style_options(name)
    - Fallbacks: "minimal" → erster PRESETS-Eintrag → DEFAULT_STYLE
    """
    # 1) Direkter Dict
    if isinstance(style_like, dict):
        return style_like

    # 2) Benannter Style
    if isinstance(style_like, str):
        s = get_style_options(style_like) or {}
        if _has_required_keys(s):
            return s

    # 3) Fallback: "minimal"
    s = get_style_options("minimal") or {}
    if _has_required_keys(s):
        return s

    # 4) Fallback: erster Eintrag in PRESETS
    for k in (PRESETS or {}).keys():
        s = get_style_options(k) or {}
        if _has_required_keys(s):
            return s

    # 5) Letzte Rettung
    return DEFAULT_STYLE
