# -*- coding: utf-8 -*-
"""
backend/llm_api.py
==================
LLM-Provider Management API.

Endpoints:
  GET  /llm/status          Aktiver Provider + Modell + Verfügbarkeit
  GET  /llm/providers       Alle Provider mit Status
  GET  /llm/models          Verfügbare Modelle (Ollama lokal)
  POST /llm/test            Test-Prompt senden
  POST /llm/switch          Provider zur Laufzeit wechseln
  GET  /llm/nemotron/info   Nemotron-spezifische Infos + Setup-Anleitung

Author: StratGen Sprint 9
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


# ── Request Models ────────────────────────────────────────────────────────────

class TestPromptRequest(BaseModel):
    prompt: str = Field(default="Antworte in einem Satz: Was ist eine SWOT-Analyse?")
    max_tokens: int = Field(default=150, ge=1, le=4096)
    provider: str | None = Field(default=None, description="Provider überschreiben")
    model: str | None = Field(default=None, description="Modell überschreiben")
    stream: bool = Field(default=False)


class SwitchProviderRequest(BaseModel):
    provider: str = Field(..., description="ollama | openai | anthropic | nemotron")
    model: str | None = Field(default=None, description="Optionales Modell")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
def get_status():
    """Aktiver LLM-Provider mit vollständigem Status."""
    from services.llm_router import get_active_provider
    info = get_active_provider()
    return JSONResponse({"ok": True, **info})


@router.get("/providers")
def list_providers():
    """Alle konfigurierten Provider mit Verfügbarkeitsstatus."""
    from services.llm_router import list_providers as _list
    providers = _list()
    return JSONResponse({"ok": True, "providers": providers})


@router.get("/models")
def list_models():
    """
    Verfügbare Modelle.
    Für Ollama: lokale Modelle werden live abgefragt.
    Für andere Provider: konfiguriertes Modell.
    """
    from services.llm_router import list_ollama_models, get_provider, get_model

    provider = get_provider()
    models = []

    if provider == "ollama":
        local = list_ollama_models()
        models = [{"name": m, "provider": "ollama", "local": True} for m in local]
    elif provider == "openai":
        models = [
            {"name": "gpt-4o", "provider": "openai", "local": False},
            {"name": "gpt-4o-mini", "provider": "openai", "local": False},
            {"name": "gpt-4-turbo", "provider": "openai", "local": False},
        ]
    elif provider == "anthropic":
        models = [
            {"name": "claude-3-5-sonnet-20241022", "provider": "anthropic", "local": False},
            {"name": "claude-3-5-haiku-20241022", "provider": "anthropic", "local": False},
            {"name": "claude-3-opus-20240229", "provider": "anthropic", "local": False},
        ]
    elif provider == "nemotron":
        use_ollama = os.getenv("NEMOTRON_USE_OLLAMA", "false").lower() == "true"
        if use_ollama:
            local = list_ollama_models()
            models = [{"name": m, "provider": "nemotron/ollama", "local": True}
                      for m in local if "nemotron" in m.lower() or "nvidia" in m.lower()]
            if not models:
                models = [{"name": m, "provider": "nemotron/ollama", "local": True}
                          for m in local]
        else:
            models = [
                {"name": "nvidia/nemotron-mini-4b-instruct",
                 "provider": "nemotron/nim", "local": False,
                 "description": "Nemotron Mini 4B – schnell, effizient"},
                {"name": "nvidia/nemotron-3-8b-chat",
                 "provider": "nemotron/nim", "local": False,
                 "description": "Nemotron 3 8B – balanciert"},
                {"name": "nvidia/nemotron-super-49b-v1",
                 "provider": "nemotron/nim", "local": False,
                 "description": "Nemotron Super 49B – höchste Qualität"},
            ]

    return JSONResponse({
        "ok": True,
        "provider": provider,
        "active_model": get_model(provider),
        "models": models,
    })


@router.post("/test")
def test_prompt(body: TestPromptRequest):
    """
    Sendet einen Test-Prompt an den LLM und misst die Antwortzeit.
    Nützlich um zu prüfen ob ein Provider/Modell funktioniert.
    """
    from services.llm_router import llm_generate, llm_stream, get_provider
    import time

    if body.stream:
        def _gen():
            for token in llm_stream(
                body.prompt,
                max_tokens=body.max_tokens,
                provider=body.provider,
                model=body.model,
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_gen(), media_type="text/event-stream")

    start = time.time()
    response = llm_generate(
        body.prompt,
        max_tokens=body.max_tokens,
        provider=body.provider,
        model=body.model,
    )
    elapsed = round(time.time() - start, 2)

    if not response:
        return JSONResponse({
            "ok": False,
            "error": "Keine Antwort vom LLM. Provider erreichbar?",
            "provider": body.provider or get_provider(),
            "elapsed_s": elapsed,
        }, status_code=503)

    return JSONResponse({
        "ok": True,
        "prompt": body.prompt,
        "response": response,
        "tokens_approx": len(response.split()),
        "elapsed_s": elapsed,
        "provider": body.provider or get_provider(),
        "model": body.model,
    })


@router.post("/switch")
def switch_provider(body: SwitchProviderRequest):
    """
    Wechselt den aktiven LLM-Provider zur Laufzeit.
    Schreibt die ENV-Variable für den aktuellen Prozess.
    Hinweis: Nach Neustart gelten wieder die .env-Werte.
    """
    valid = {"ollama", "openai", "anthropic", "nemotron"}
    if body.provider not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiger Provider '{body.provider}'. Gültig: {sorted(valid)}"
        )

    os.environ["LLM_PROVIDER"] = body.provider
    if body.model:
        os.environ["LLM_MODEL"] = body.model

    from services.llm_router import get_active_provider
    info = get_active_provider()

    log.info("LLM Provider gewechselt zu: %s / %s", body.provider, body.model)

    return JSONResponse({
        "ok": True,
        "message": f"Provider auf '{body.provider}' gewechselt.",
        "active": info,
    })


@router.get("/nemotron/info")
def nemotron_info():
    """
    Informationen zu Nvidia Nemotron 3 Super und Setup-Anleitung.
    """
    use_ollama = os.getenv("NEMOTRON_USE_OLLAMA", "false").lower() == "true"
    nim_key_set = bool(os.getenv("NVIDIA_API_KEY"))

    return JSONResponse({
        "ok": True,
        "model_family": "Nvidia Nemotron 3 Super",
        "description": (
            "Nvidia Nemotron 3 Super ist eine Open-Source-LLM-Familie von Nvidia, "
            "optimiert für Reasoning und Effizienz auf NVIDIA-Hardware. "
            "Verfügbar via Nvidia NIM API oder lokal via Ollama."
        ),
        "models": {
            "nemotron-mini-4b-instruct": "Kleinstes Modell, sehr schnell",
            "nemotron-3-8b-chat": "Balanciert: Qualität + Geschwindigkeit",
            "nemotron-super-49b-v1": "Größtes Modell, höchste Qualität",
        },
        "current_config": {
            "use_ollama": use_ollama,
            "nim_key_set": nim_key_set,
            "model": os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-mini-4b-instruct"),
            "nim_host": os.getenv("NEMOTRON_HOST", "https://integrate.api.nvidia.com/v1"),
        },
        "setup": {
            "option_a_nim": {
                "description": "Nvidia NIM API (empfohlen, kein lokales Setup)",
                "steps": [
                    "1. API-Key holen: https://build.nvidia.com",
                    "2. NVIDIA_API_KEY=nvapi-... in .env setzen",
                    "3. LLM_PROVIDER=nemotron in .env setzen",
                    "4. NEMOTRON_MODEL=nvidia/nemotron-mini-4b-instruct setzen",
                    "5. Service neu starten",
                ],
                "env": {
                    "LLM_PROVIDER": "nemotron",
                    "NVIDIA_API_KEY": "nvapi-...",
                    "NEMOTRON_MODEL": "nvidia/nemotron-mini-4b-instruct",
                },
            },
            "option_b_ollama": {
                "description": "Lokal via Ollama (Privacy-First, GPU empfohlen)",
                "steps": [
                    "1. ollama pull nemotron-mini",
                    "2. LLM_PROVIDER=nemotron in .env setzen",
                    "3. NEMOTRON_USE_OLLAMA=true in .env setzen",
                    "4. NEMOTRON_OLLAMA_MODEL=nemotron-mini setzen",
                    "5. Service neu starten",
                ],
                "env": {
                    "LLM_PROVIDER": "nemotron",
                    "NEMOTRON_USE_OLLAMA": "true",
                    "NEMOTRON_OLLAMA_MODEL": "nemotron-mini",
                },
            },
        },
        "links": {
            "nim_catalog": "https://build.nvidia.com/nvidia/nemotron-mini-4b-instruct",
            "ollama_model": "https://ollama.com/library/nemotron-mini",
            "github": "https://github.com/NVIDIA/NeMo",
        },
    })

@router.get("/local-models")
def get_local_models():
    """
    Zeigt alle verfügbaren lokalen Ollama-Modelle mit empfohlenen Rollen.
    Nützlich um den Refiner optimal zu konfigurieren.
    """
    from services.llm_router import get_available_local_models
    models = get_available_local_models()
    return JSONResponse({
        "ok": True,
        "models": models,
        "recommended_config": {
            "refiner": {
                "generator_provider": "ollama",
                "generator_model": models.get("generator") or "llama3:8b",
                "critic_provider": "ollama",
                "critic_model": models.get("critic") or "mistral",
            },
            "embeddings": models.get("embeddings"),
            "vision": models.get("vision"),
        },
        "tip": (
            "Generator und Critic sollten verschiedene Modelle sein "
            "für echte Perspektivvielfalt. "
            f"Empfehlung: Generator={models.get('generator')}, "
            f"Critic={models.get('critic')}"
        ),
    })


@router.post("/vision/analyze")
async def analyze_image(
    file: "UploadFile" = None,
    image_path: str = None,
    prompt: str = "Beschreibe dieses Bild. Nenne Themen, Objekte, Keywords für Strategie-Präsentationen.",
):
    """
    Analysiert ein Bild mit Moondream (lokal).
    Entweder Datei hochladen oder Pfad angeben.
    """
    from services.llm_router import llm_vision, get_vision_model
    from fastapi import UploadFile
    import tempfile, os

    tmp_path = None
    try:
        if file:
            suffix = os.path.splitext(file.filename or "img.jpg")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            path_to_analyze = tmp_path
        elif image_path:
            path_to_analyze = image_path
        else:
            return JSONResponse({"ok": False, "error": "file oder image_path erforderlich"}, status_code=400)

        result = llm_vision(path_to_analyze, prompt)
        return JSONResponse({
            "ok": True,
            "model": get_vision_model(),
            "description": result,
            "image_path": image_path or file.filename,
        })
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
