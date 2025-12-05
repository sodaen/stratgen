"""
Settings API für Stratgen.
Speichert und lädt Benutzereinstellungen.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

SETTINGS_FILE = Path("/home/sodaen/stratgen/data/settings.json")


class LLMSettings(BaseModel):
    model: str = "mistral:latest"
    max_tokens: int = 4096
    timeout: int = 120


class GenerationSettings(BaseModel):
    default_slides: int = 10
    temperature: float = 0.7
    style: str = "corporate"
    auto_save: bool = True


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {}


def save_settings(settings: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


@router.get("")
async def get_settings():
    """Alle Einstellungen abrufen."""
    return {"ok": True, "settings": load_settings()}


@router.post("/llm")
async def set_llm_settings(settings: LLMSettings):
    """LLM Einstellungen speichern."""
    current = load_settings()
    current["llm"] = settings.dict()
    save_settings(current)
    
    # Tatsächlich anwenden: Update global config
    import os
    os.environ["STRATGEN_LLM_MODEL"] = settings.model
    os.environ["STRATGEN_LLM_MAX_TOKENS"] = str(settings.max_tokens)
    os.environ["STRATGEN_LLM_TIMEOUT"] = str(settings.timeout)
    
    logger.info(f"LLM settings updated: {settings.model}")
    return {"ok": True, "message": "LLM settings saved"}


@router.post("/generation")
async def set_generation_settings(settings: GenerationSettings):
    """Generierungs-Einstellungen speichern."""
    current = load_settings()
    current["generation"] = settings.dict()
    save_settings(current)
    
    logger.info(f"Generation settings updated")
    return {"ok": True, "message": "Generation settings saved"}


@router.get("/llm")
async def get_llm_settings():
    """Aktuelle LLM Einstellungen."""
    settings = load_settings()
    return {"ok": True, "settings": settings.get("llm", LLMSettings().dict())}


@router.get("/generation")
async def get_generation_settings():
    """Aktuelle Generierungs-Einstellungen."""
    settings = load_settings()
    return {"ok": True, "settings": settings.get("generation", GenerationSettings().dict())}
