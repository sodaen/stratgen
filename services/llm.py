from __future__ import annotations
from typing import Optional, Dict, Any
import os, json, time, requests

# ENV:
#   LLM_PROVIDER=ollama   (aktiviert Nutzung dieses Clients)
#   OLLAMA_HOST=http://127.0.0.1:11434
#   LLM_MODEL=mistral     (Default)
#   LLM_TEMPERATURE=0.4
#   LLM_MAX_TOKENS=512

def _cfg(key: str, default: Optional[str]=None) -> str:
    v = os.environ.get(key, default)
    return "" if v is None else str(v)

def is_enabled() -> bool:
    return _cfg("LLM_PROVIDER","").lower() == "ollama"

def _host() -> str:
    return _cfg("OLLAMA_HOST","http://127.0.0.1:11434")

def _model() -> str:
    return _cfg("LLM_MODEL","mistral")

def health() -> Dict[str, Any]:
    try:
        r = requests.get(_host()+"/api/tags", timeout=3)
        r.raise_for_status()
        return {"ok": True, "models": [m.get("name") for m in r.json().get("models",[])]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def generate(prompt: str,
             model: Optional[str]=None,
             temperature: Optional[float]=None,
             max_tokens: Optional[int]=None,
             system: Optional[str]=None) -> Dict[str, Any]:
    """Synchronous (non-stream) text generation via Ollama."""
    if not is_enabled():
        return {"ok": False, "error": "LLM disabled (LLM_PROVIDER!=ollama)"}
    payload = {
        "model": model or _model(),
        "prompt": prompt,
        "stream": False,
        "options": {}
    }
    temp = temperature if temperature is not None else float(_cfg("LLM_TEMPERATURE","0.4"))
    if temp is not None:
        payload["options"]["temperature"] = float(temp)
    mx = max_tokens or int(_cfg("LLM_MAX_TOKENS","512"))
    if mx: payload["options"]["num_predict"] = int(mx)
    if system:
        payload["system"] = system

    try:
        t0 = time.time()
        r = requests.post(_host()+"/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return {
            "ok": True,
            "model": payload["model"],
            "response": data.get("response",""),
            "total_duration_ms": int((time.time()-t0)*1000),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
