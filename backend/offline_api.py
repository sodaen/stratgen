# -*- coding: utf-8 -*-
"""
StratGen – Offline Mode API (Sprint 4)
Status anzeigen + Offline-Mode zur Laufzeit schalten.

Endpoints:
  GET  /offline/status          – Aktueller Status
  POST /offline/enable          – Offline-Mode einschalten
  POST /offline/disable         – Offline-Mode ausschalten
  POST /offline/reset           – Runtime-Override zurücksetzen
  GET  /offline/health          – Kurzcheck aller externen Services (live)
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

log = logging.getLogger("stratgen.offline_api")
router = APIRouter(prefix="/offline", tags=["offline"])


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.get("/status")
def get_offline_status():
    """Gibt Offline-Mode Status zurück."""
    from services.offline import get_status
    return get_status()


class OfflineToggle(BaseModel):
    reason: str = ""


@router.post("/enable")
def enable_offline(body: OfflineToggle = None):
    """Schaltet Offline-Mode ein (ohne Neustart)."""
    from services.offline import set_offline
    set_offline(True)
    log.warning("Offline mode ENABLED via API. Reason: %s", (body.reason if body else ""))
    return {
        "ok": True,
        "offline_mode": True,
        "message": "Offline-Mode aktiviert. Alle externen Calls deaktiviert.",
    }


@router.post("/disable")
def disable_offline(body: OfflineToggle = None):
    """Schaltet Offline-Mode aus."""
    from services.offline import set_offline
    set_offline(False)
    return {
        "ok": True,
        "offline_mode": False,
        "message": "Offline-Mode deaktiviert. Externe Services wieder erreichbar.",
    }


@router.post("/reset")
def reset_offline():
    """Setzt Runtime-Override zurück → ENV-Variable STRATGEN_OFFLINE gilt wieder."""
    from services.offline import reset_override, is_offline
    reset_override()
    return {
        "ok": True,
        "offline_mode": is_offline(),
        "message": "Runtime-Override zurückgesetzt. ENV-Variable gilt wieder.",
    }


@router.get("/health")
def offline_health_check():
    """
    Live-Check aller externen Services.
    Funktioniert auch im Offline-Mode (zeigt dann 'blocked').
    """
    from services.offline import is_offline, offline_result

    offline = is_offline()
    results: Dict[str, Any] = {}
    overall_ok = True

    # 1. Ollama
    if offline:
        results["ollama"] = {"ok": None, "blocked": True, "latency_ms": None}
    else:
        try:
            import requests
            ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
            t0 = time.time()
            r = requests.get(f"{ollama_host}/api/tags", timeout=3)
            ms = int((time.time() - t0) * 1000)
            models = [m.get("name") for m in (r.json().get("models") or [])]
            results["ollama"] = {"ok": r.ok, "latency_ms": ms, "models": models[:5]}
        except Exception as e:
            results["ollama"] = {"ok": False, "error": str(e)[:80]}
            overall_ok = False

    # 2. Qdrant (lokal – immer prüfen)
    try:
        import requests
        qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
        t0 = time.time()
        r = requests.get(f"{qdrant_url}/readyz", timeout=3)
        ms = int((time.time() - t0) * 1000)
        results["qdrant"] = {"ok": r.ok, "latency_ms": ms}
    except Exception as e:
        results["qdrant"] = {"ok": False, "error": str(e)[:80]}
        overall_ok = False

    # 3. World Bank
    if offline:
        results["world_bank"] = {"ok": None, "blocked": True}
    else:
        try:
            import requests
            t0 = time.time()
            r = requests.get(
                "https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.MKTP.CD",
                params={"format": "json", "per_page": "1"},
                timeout=5,
            )
            ms = int((time.time() - t0) * 1000)
            results["world_bank"] = {"ok": r.ok, "latency_ms": ms}
        except Exception as e:
            results["world_bank"] = {"ok": False, "error": str(e)[:80]}

    # 4. OpenAI (nur prüfen ob Key gesetzt, kein echten Call)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    results["openai"] = {
        "ok": bool(openai_key),
        "key_set": bool(openai_key),
        "blocked": offline,
    }

    # 5. Redis
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        t0 = time.time()
        r_client = redis.from_url(redis_url, socket_connect_timeout=2)
        r_client.ping()
        ms = int((time.time() - t0) * 1000)
        results["redis"] = {"ok": True, "latency_ms": ms}
    except Exception as e:
        results["redis"] = {"ok": False, "error": str(e)[:60]}

    return {
        "ok": overall_ok,
        "offline_mode": offline,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "services": results,
    }
