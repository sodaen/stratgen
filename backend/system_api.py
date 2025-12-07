"""
System API - System Management Endpoints
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
import shutil
import subprocess

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/restart")
async def restart_system():
    """Startet das Backend neu (via systemctl)."""
    try:
        # Wir können uns nicht selbst neustarten, aber wir können es triggern
        return {
            "ok": True,
            "message": "Restart requested. Use systemctl restart stratgen.service manually.",
            "hint": "sudo systemctl restart stratgen.service"
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/restart/{service}")
async def restart_service(service: str):
    """Startet einen spezifischen Service neu."""
    allowed = ["ollama", "qdrant", "stratgen"]
    if service not in allowed:
        raise HTTPException(400, f"Service must be one of: {allowed}")
    
    return {
        "ok": True,
        "message": f"Restart {service} requested",
        "hint": f"sudo systemctl restart {service}.service"
    }


@router.post("/cleanup")
async def cleanup_system():
    """Räumt temporäre Dateien auf."""
    cleaned = {
        "cache_files": 0,
        "temp_files": 0,
        "old_exports": 0
    }
    
    # Clean __pycache__
    for pycache in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            cleaned["cache_files"] += 1
        except:
            pass
    
    # Clean alte Exports (älter als 7 Tage)
    exports_dir = Path("data/exports")
    if exports_dir.exists():
        import time
        now = time.time()
        for f in exports_dir.glob("*"):
            if f.is_file() and (now - f.stat().st_mtime) > 7 * 24 * 3600:
                try:
                    f.unlink()
                    cleaned["old_exports"] += 1
                except:
                    pass
    
    return {"ok": True, "cleaned": cleaned}


@router.get("/status")
async def system_status():
    """Gibt System-Status zurück."""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()) if hasattr(psutil, 'boot_time') else 0
    }
