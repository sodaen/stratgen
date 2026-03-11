# -*- coding: utf-8 -*-
"""
StratGen – Offline Mode (Sprint 4)
====================================
Zentrales Modul das alle externen Calls kontrolliert.

ENV-Flag:
  STRATGEN_OFFLINE=true   → Alle externen HTTP-Calls deaktiviert
  STRATGEN_OFFLINE=false  → Normal (Default)

Nutzung in jedem Service:
  from services.offline import is_offline, offline_result, require_online

Funktionen:
  is_offline()         → bool
  offline_result(name) → {"ok": False, "offline": True, "service": name}
  require_online(name) → raises OfflineError wenn OFFLINE=true
  guard(name)          → Decorator für ganze Funktionen

Status-Endpoint: GET /offline/status
"""
from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

log = logging.getLogger("stratgen.offline")

# ─────────────────────────────────────────────
# OFFLINE STATE
# ─────────────────────────────────────────────

_OVERRIDE: Optional[bool] = None   # Kann per API zur Laufzeit gesetzt werden
_started_at = time.time()


def is_offline() -> bool:
    """
    Prüft ob Offline-Mode aktiv ist.
    Priorität: 1. Runtime-Override  2. ENV-Variable
    """
    if _OVERRIDE is not None:
        return _OVERRIDE
    val = os.getenv("STRATGEN_OFFLINE", "false").strip().lower()
    return val in ("1", "true", "yes", "on")


def set_offline(value: bool):
    """Setzt Offline-Mode zur Laufzeit (ohne Neustart)."""
    global _OVERRIDE
    _OVERRIDE = value
    log.warning("Offline mode %s via runtime override", "ENABLED" if value else "DISABLED")


def reset_override():
    """Setzt Runtime-Override zurück → ENV-Variable gilt wieder."""
    global _OVERRIDE
    _OVERRIDE = None


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

class OfflineError(RuntimeError):
    """Wird geworfen wenn ein Dienst im Offline-Mode aufgerufen wird."""
    def __init__(self, service: str = ""):
        self.service = service
        super().__init__(f"Service '{service}' ist im Offline-Modus nicht verfügbar")


def offline_result(service: str, message: str = "") -> Dict[str, Any]:
    """Gibt ein standardisiertes Offline-Ergebnis zurück."""
    return {
        "ok": False,
        "offline": True,
        "service": service,
        "message": message or f"{service} ist im Offline-Modus nicht verfügbar",
    }


def require_online(service: str = ""):
    """Wirft OfflineError wenn OFFLINE=true. Für kritische Calls."""
    if is_offline():
        raise OfflineError(service)


def guard(service_name: str, fallback: Any = None):
    """
    Decorator: Gibt fallback zurück wenn offline.

    Verwendung:
        @guard("world_bank", fallback={"ok": False, "data": []})
        def get_world_bank_data(...):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if is_offline():
                log.debug("OFFLINE: %s skipped", service_name)
                if fallback is not None:
                    return fallback
                return offline_result(service_name)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# SERVICE STATUS (für Health-Check)
# ─────────────────────────────────────────────

# Registry der bekannten externen Services
_SERVICES = {
    "world_bank":   {"description": "World Bank API",        "required": False},
    "ollama":       {"description": "Ollama LLM",            "required": False},
    "openai":       {"description": "OpenAI API",            "required": False},
    "anthropic":    {"description": "Anthropic API",         "required": False},
    "qdrant":       {"description": "Qdrant Vector DB",      "required": True},
    "redis":        {"description": "Redis / Celery",        "required": False},
}


def get_status() -> Dict[str, Any]:
    """Gibt aktuellen Offline-Status zurück."""
    offline = is_offline()
    return {
        "offline_mode": offline,
        "source": "runtime_override" if _OVERRIDE is not None else "env",
        "env_value": os.getenv("STRATGEN_OFFLINE", "false"),
        "uptime_seconds": int(time.time() - _started_at),
        "services": {
            name: {
                **info,
                "blocked": offline and not name == "qdrant",
            }
            for name, info in _SERVICES.items()
        },
        "message": (
            "Alle externen HTTP-Calls deaktiviert. Ollama/OpenAI/WorldBank nicht erreichbar."
            if offline else
            "Online – alle externen Services erreichbar."
        ),
    }
