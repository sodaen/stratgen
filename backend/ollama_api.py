"""
Ollama API - Ollama Management Endpoints
"""
from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter(prefix="/ollama", tags=["ollama"])

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


@router.get("/models")
async def list_models():
    """Liste aller verfügbaren Ollama Modelle."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "ok": True,
                    "models": models,
                    "count": len(models)
                }
            return {"ok": False, "error": f"Status {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e), "models": []}


@router.get("/status")
async def ollama_status():
    """Prüft ob Ollama erreichbar ist."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "ok": True,
                    "host": OLLAMA_HOST,
                    "models_count": len(data.get("models", []))
                }
    except:
        pass
    return {"ok": False, "host": OLLAMA_HOST}


@router.post("/pull/{model}")
async def pull_model(model: str):
    """Lädt ein Modell herunter."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/pull",
                json={"name": model},
                timeout=300
            )
            return {"ok": resp.status_code == 200, "model": model}
    except Exception as e:
        raise HTTPException(500, str(e))
