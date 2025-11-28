# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from services.style_presets import PRESETS, get_style_options

router = APIRouter(prefix="/styles", tags=["styles"])

@router.get("", summary="Liste aller Styles")
def list_styles() -> Dict[str, Any]:
    out = {}
    for name in PRESETS.keys():
        opts = get_style_options(name)
        out[name] = {
            "name": name,
            "options": opts,
        }
    return {"styles": out}

@router.get("/{name}", summary="Details zu einem Style")
def get_style(name: str) -> Dict[str, Any]:
    if name not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Style '{name}' nicht gefunden")
    return {"name": name, "options": get_style_options(name)}
