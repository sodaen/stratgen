"""
QA/Quality Assurance API für Stratgen.
Nutzt critic.py für Präsentations-Qualitätsprüfung.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/critique")
async def critique_presentation(data: Dict[str, Any]):
    """
    Prüft eine Präsentation auf Qualität.
    
    Erwartet:
    - title: Präsentationstitel
    - slides: Liste von Slides
    """
    try:
        from services.critic import _critique_strategy
        
        result = _critique_strategy(data)
        return {
            "ok": True,
            "score": result.get("score", 0),
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", [])
        }
    except Exception as e:
        logger.error(f"Critique failed: {e}")
        return {"ok": False, "error": str(e)}


@router.get("/status")
async def qa_status():
    """Gibt QA-Service Status zurück."""
    return {
        "ok": True,
        "service": "qa",
        "features": ["critique", "validate"]
    }
