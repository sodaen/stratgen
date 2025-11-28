from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
import json

router = APIRouter(tags=["learn"])

# Importpfade tolerant handhaben: prefer learn_engine, fallback learn
try:
    from services.learn_engine import scan_and_learn, stats
except Exception:  # pragma: no cover
    from services.learn import scan_and_learn, stats  # type: ignore

@router.post("/scan")
@router.get("/scan")
def learn_scan() -> Dict[str, Any]:
    """
    Scannt data/raw und data/exports und lernt neu gefundene PPTX/PPT.
    """
    dirs = ["data/raw", "data/exports"]
    out = scan_and_learn(dirs)
    return out

@router.get("/stats")
def learn_stats() -> Dict[str, Any]:
    """
    Liefert einfache Statistik zu gelernten Artefakten.
    """
    return stats()
