from __future__ import annotations


import json
import urllib.request
import urllib.error
from typing import Optional


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


def generate_local_llm(prompt: str, model: str = "mistral", max_tokens: int = 512) -> str:
    """
    Versucht, lokal Ollama anzusprechen.
    Fallback: gibt einen generischen Text zurück.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            return parsed.get("response") or parsed.get("text") or ""
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionRefusedError):
        # Fallback: heuristischer Text
        return (
            "Ollama/Mistral nicht erreichbar. "
            "Fallback: Bitte lokalen LLM starten (ollama run mistral). "
            "Vorläufige Strategie: 1) Zielgruppe definieren 2) Kanäle festlegen 3) Kernbotschaften 4) Contentplan 5) KPIs."
        )
