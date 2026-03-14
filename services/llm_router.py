# -*- coding: utf-8 -*-
"""
services/llm_router.py
=======================
Zentraler LLM-Router für StratGen.

Unterstützte Provider:
  - ollama      Lokales Ollama (Standard, Privacy-First)
  - openai      OpenAI API (GPT-4o, GPT-4o-mini, ...)
  - anthropic   Anthropic API (Claude 3.5 Sonnet, ...)
  - nemotron    Nvidia Nemotron 3 Super via Nvidia NIM API
                (auch lokal via Ollama wenn Modell verfügbar)

Verwendung (Drop-In-Ersatz für bisherige _llm_generate() Funktionen):

    from services.llm_router import llm_generate, llm_stream, get_active_provider

    # Einfacher Call
    result = llm_generate("Analysiere SWOT für Tesla", max_tokens=500)

    # Streaming (Generator)
    for token in llm_stream("Schreibe eine Einleitung"):
        print(token, end="", flush=True)

    # Provider-Info
    info = get_active_provider()
    # → {"provider": "nemotron", "model": "nemotron-3-8b", "ok": True}

ENV-Variablen:
    LLM_PROVIDER          ollama | openai | anthropic | nemotron (default: ollama)
    LLM_MODEL             Modell-Name (provider-spezifisch)
    LLM_TEMPERATURE       Temperatur 0.0–1.0 (default: 0.7)
    LLM_MAX_TOKENS        Max Output-Tokens (default: 1024)

    # Ollama
    OLLAMA_HOST           http://127.0.0.1:11434

    # OpenAI
    OPENAI_API_KEY        sk-...
    OPENAI_MODEL          gpt-4o-mini

    # Anthropic
    ANTHROPIC_API_KEY     sk-ant-...
    ANTHROPIC_MODEL       claude-3-5-haiku-20241022

    # Nvidia Nemotron (NIM API)
    NVIDIA_API_KEY        nvapi-...
    NEMOTRON_MODEL        nvidia/nemotron-mini-4b-instruct
    NEMOTRON_HOST         https://integrate.api.nvidia.com/v1  (NIM API)
                          oder http://127.0.0.1:11434           (lokal via Ollama)
    NEMOTRON_USE_OLLAMA   true | false  (lokal via Ollama statt NIM)

Author: StratGen Sprint 9
"""
from __future__ import annotations

import logging
import os
from typing import Generator, Optional

import requests

log = logging.getLogger(__name__)

# ── Konfiguration ─────────────────────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def get_provider() -> str:
    return _cfg("LLM_PROVIDER", "ollama").lower()


def get_model(provider: Optional[str] = None) -> str:
    p = provider or get_provider()
    defaults = {
        "ollama":    "mistral",
        "openai":    "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "nemotron":  "nvidia/nemotron-mini-4b-instruct",
    }
    env_model = _cfg("LLM_MODEL") or _cfg(f"{p.upper()}_MODEL")
    return env_model or defaults.get(p, "mistral")


def get_temperature() -> float:
    try:
        return float(_cfg("LLM_TEMPERATURE", "0.7"))
    except ValueError:
        return 0.7


def get_max_tokens() -> int:
    try:
        return int(_cfg("LLM_MAX_TOKENS", "1024"))
    except ValueError:
        return 1024


# ── Offline Guard ─────────────────────────────────────────────────────────────

def _is_offline() -> bool:
    try:
        from services.offline import is_offline
        return is_offline()
    except ImportError:
        return _cfg("STRATGEN_OFFLINE", "false").lower() == "true"


# ── Provider-Implementierungen ────────────────────────────────────────────────

def _call_ollama(prompt: str, max_tokens: int, temperature: float,
                 model: Optional[str] = None, stream: bool = False):
    host  = _cfg("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = model or get_model("ollama")
    payload = {
        "model":  model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }
    r = requests.post(f"{host}/api/generate", json=payload, timeout=180,
                      stream=stream)
    r.raise_for_status()
    if stream:
        return r
    return (r.json().get("response") or "").strip()


def _call_openai(prompt: str, max_tokens: int, temperature: float,
                 model: Optional[str] = None, stream: bool = False) -> str:
    api_key = _cfg("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY nicht gesetzt")
    model = model or get_model("openai")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=120,
        stream=stream,
    )
    r.raise_for_status()
    if stream:
        return r
    return (r.json()["choices"][0]["message"]["content"] or "").strip()


def _call_anthropic(prompt: str, max_tokens: int, temperature: float,
                    model: Optional[str] = None, stream: bool = False) -> str:
    api_key = _cfg("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
    model = model or get_model("anthropic")
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
    }
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
        stream=stream,
    )
    r.raise_for_status()
    if stream:
        return r
    data = r.json()
    return (data.get("content", [{}])[0].get("text") or "").strip()


def _call_nemotron(prompt: str, max_tokens: int, temperature: float,
                   model: Optional[str] = None, stream: bool = False):
    """
    Nvidia Nemotron 3 Super via:
    A) Nvidia NIM API (NVIDIA_API_KEY gesetzt)
    B) Lokal via Ollama (NEMOTRON_USE_OLLAMA=true)
    """
    use_ollama = _cfg("NEMOTRON_USE_OLLAMA", "false").lower() == "true"
    model = model or get_model("nemotron")

    if use_ollama:
        # Lokal via Ollama – Modell muss mit `ollama pull` geladen sein
        # z.B. ollama pull nemotron-mini
        ollama_model = _cfg("NEMOTRON_OLLAMA_MODEL", model.split("/")[-1])
        host = _cfg("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        r = requests.post(f"{host}/api/generate", json=payload,
                          timeout=180, stream=stream)
        r.raise_for_status()
        if stream:
            return r
        return (r.json().get("response") or "").strip()

    # Nvidia NIM API (OpenAI-kompatibel)
    api_key = _cfg("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY nicht gesetzt. "
            "Alternativ NEMOTRON_USE_OLLAMA=true für lokale Nutzung."
        )

    nim_host = _cfg("NEMOTRON_HOST", "https://integrate.api.nvidia.com/v1")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    r = requests.post(
        f"{nim_host}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
        stream=stream,
    )
    r.raise_for_status()
    if stream:
        return r
    return (r.json()["choices"][0]["message"]["content"] or "").strip()


# ── Haupt-Funktionen ──────────────────────────────────────────────────────────

def llm_generate(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Zentrale LLM-Funktion. Drop-In-Ersatz für bisherige _llm_generate().

    Args:
        prompt:      Der Prompt-Text
        max_tokens:  Max Output-Tokens (default: LLM_MAX_TOKENS env)
        temperature: Sampling-Temperatur (default: LLM_TEMPERATURE env)
        provider:    Provider überschreiben (default: LLM_PROVIDER env)
        model:       Modell überschreiben (default: LLM_MODEL env)

    Returns:
        Generierter Text als String.
        Bei Fehler: leerer String (kein raise, damit Fallbacks funktionieren).
    """
    if _is_offline():
        log.info("LLM-Call übersprungen (Offline-Mode)")
        return ""

    p    = (provider or get_provider()).lower()
    mt   = max_tokens   or get_max_tokens()
    temp = temperature  or get_temperature()

    try:
        if p == "ollama":
            return _call_ollama(prompt, mt, temp, model)
        elif p == "openai":
            return _call_openai(prompt, mt, temp, model)
        elif p == "anthropic":
            return _call_anthropic(prompt, mt, temp, model)
        elif p == "nemotron":
            return _call_nemotron(prompt, mt, temp, model)
        else:
            log.warning("Unbekannter LLM-Provider '%s', fallback Ollama", p)
            return _call_ollama(prompt, mt, temp, model)
    except Exception as e:
        log.error("LLM-Call fehlgeschlagen (%s/%s): %s", p, model or get_model(p), e)
        return ""


def llm_stream(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Streaming-Variante. Gibt Token für Token als Generator zurück.
    Für SSE-Endpoints gedacht.
    """
    import json

    if _is_offline():
        yield ""
        return

    p    = (provider or get_provider()).lower()
    mt   = max_tokens   or get_max_tokens()
    temp = temperature  or get_temperature()

    try:
        if p == "ollama" or (p == "nemotron" and
                             _cfg("NEMOTRON_USE_OLLAMA", "false") == "true"):
            r = _call_ollama(prompt, mt, temp, model, stream=True) if p == "ollama" \
                else _call_nemotron(prompt, mt, temp, model, stream=True)
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass

        elif p in ("openai", "nemotron"):
            r = _call_openai(prompt, mt, temp, model, stream=True) if p == "openai" \
                else _call_nemotron(prompt, mt, temp, model, stream=True)
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    raw = line[6:]
                    if raw == b"[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                        token = data["choices"][0].get("delta", {}).get("content", "")
                        if token:
                            yield token
                    except (json.JSONDecodeError, KeyError):
                        pass

        elif p == "anthropic":
            r = _call_anthropic(prompt, mt, temp, model, stream=True)
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    raw = line[6:]
                    try:
                        data = json.loads(raw)
                        if data.get("type") == "content_block_delta":
                            token = data.get("delta", {}).get("text", "")
                            if token:
                                yield token
                    except json.JSONDecodeError:
                        pass

    except Exception as e:
        log.error("LLM-Stream fehlgeschlagen (%s): %s", p, e)
        yield ""


# ── Provider-Info ─────────────────────────────────────────────────────────────

def get_active_provider() -> dict:
    """Gibt Informationen über den aktiven Provider zurück."""
    p = get_provider()
    m = get_model(p)

    info = {
        "provider": p,
        "model": m,
        "temperature": get_temperature(),
        "max_tokens": get_max_tokens(),
        "offline": _is_offline(),
    }

    # Provider-spezifische Infos
    if p == "ollama":
        info["host"] = _cfg("OLLAMA_HOST", "http://127.0.0.1:11434")
        info["ok"] = _ping_ollama()
    elif p == "openai":
        info["key_set"] = bool(_cfg("OPENAI_API_KEY"))
        info["ok"] = info["key_set"]
    elif p == "anthropic":
        info["key_set"] = bool(_cfg("ANTHROPIC_API_KEY"))
        info["ok"] = info["key_set"]
    elif p == "nemotron":
        use_ollama = _cfg("NEMOTRON_USE_OLLAMA", "false").lower() == "true"
        info["use_ollama"] = use_ollama
        info["nim_host"] = _cfg("NEMOTRON_HOST", "https://integrate.api.nvidia.com/v1")
        if use_ollama:
            info["ok"] = _ping_ollama()
            info["ollama_model"] = _cfg("NEMOTRON_OLLAMA_MODEL", m.split("/")[-1])
        else:
            info["key_set"] = bool(_cfg("NVIDIA_API_KEY"))
            info["ok"] = info["key_set"]

    return info


def list_providers() -> list[dict]:
    """Alle konfigurierten Provider mit Status."""
    return [
        {
            "id": "ollama",
            "name": "Ollama (lokal)",
            "model": get_model("ollama"),
            "available": _ping_ollama(),
            "privacy": "high",
            "active": get_provider() == "ollama",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "model": get_model("openai"),
            "available": bool(_cfg("OPENAI_API_KEY")),
            "privacy": "low",
            "active": get_provider() == "openai",
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "model": get_model("anthropic"),
            "available": bool(_cfg("ANTHROPIC_API_KEY")),
            "privacy": "low",
            "active": get_provider() == "anthropic",
        },
        {
            "id": "nemotron",
            "name": "Nvidia Nemotron 3 Super",
            "model": get_model("nemotron"),
            "available": (
                bool(_cfg("NVIDIA_API_KEY")) or
                _cfg("NEMOTRON_USE_OLLAMA", "false").lower() == "true"
            ),
            "privacy": "high" if _cfg("NEMOTRON_USE_OLLAMA") == "true" else "medium",
            "active": get_provider() == "nemotron",
            "nim_url": "https://integrate.api.nvidia.com/v1",
            "note": "via Nvidia NIM API oder lokal via Ollama (NEMOTRON_USE_OLLAMA=true)",
        },
    ]


def _ping_ollama() -> bool:
    """Prüft ob Ollama erreichbar ist."""
    try:
        host = _cfg("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        r = requests.get(f"{host}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_ollama_models() -> list[str]:
    """Listet alle lokalen Ollama-Modelle auf."""
    try:
        host = _cfg("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        r = requests.get(f"{host}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []
