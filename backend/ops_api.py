from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import shutil, time
from services.rag_pipeline import check_qdrant, check_ollama
from services.cache import cache_clear
from qdrant_client import QdrantClient
import os

router = APIRouter(prefix="/ops", tags=["ops"])

@router.get("/status")
def status():
    return {"ok": True, "qdrant": check_qdrant(), "ollama": check_ollama()}

@router.post("/cache/clear")
def clear(prefix: Optional[str] = Body(default=None)):
    n = cache_clear(prefix)
    return {"ok": True, "cleared": n}

@router.post("/qdrant/snapshot")
def qdrant_snapshot(collection: str = "strategies"):
    try:
        host = os.getenv("QDRANT_URL","http://localhost:6333").replace("http://","").split(":")[0]
        port = int(os.getenv("QDRANT_URL","http://localhost:6333").split(":")[-1])
    except Exception:
        host, port = "localhost", 6333
    try:
        qc = QdrantClient(host=host, port=port, timeout=10)
        info = qc.create_snapshot(collection)
        # Hinweis: Snapshot-Datei liegt im Qdrant-Speicherordner (Docker-Volume)
        return JSONResponse({"ok": True, "snapshot": str(info)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


from typing import Optional
import os, json
import httpx
from pathlib import Path

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
TEMPLATE_PATH = Path("data/templates/master.pptx")
EXPORT_DIR = Path("data/exports")
BRAND_DB = Path("data/brand_store.json")

@router.get("/health")
def health():
    def check_qdrant():
        try:
            r = httpx.get(QDRANT_URL.rstrip("/") + "/readyz", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def check_ollama():
        try:
            r = httpx.get(OLLAMA_URL.rstrip("/") + "/api/tags", timeout=1.5)
            # minimal JSON-Check
            _ = r.json()
            return r.status_code == 200
        except Exception:
            return False

    def brand_count():
        try:
            if BRAND_DB.exists():
                data = json.loads(BRAND_DB.read_text(encoding="utf-8") or "{}")
                if isinstance(data, dict):
                    return len(data)
            return 0
        except Exception:
            return 0

    res = {
        "ok": True,
        "qdrant_ok": check_qdrant(),
        "ollama_ok": check_ollama(),
        "templates_ok": TEMPLATE_PATH.exists(),
        "export_dir_ok": EXPORT_DIR.exists(),
        "brand_entries": brand_count(),
    }
    # Gesamtergebnis
    res["ok"] = all([res["qdrant_ok"], res["templates_ok"], res["export_dir_ok"]])
    return res


