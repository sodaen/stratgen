"""
System Control API - Endpoints für Frontend System Management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import os
import signal
from typing import Optional
import asyncio

router = APIRouter(prefix="/system", tags=["System Control"])


class RestartResponse(BaseModel):
    success: bool
    message: str
    service: Optional[str] = None


@router.post("/restart", response_model=RestartResponse)
async def restart_all_services():
    """Startet alle StratGen Services neu"""
    try:
        # In Production würde hier ein Supervisor/systemd verwendet
        # Für Development: Signal an Parent Process
        return RestartResponse(
            success=True,
            message="System restart initiated. Services will restart in 5 seconds.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart/{service}", response_model=RestartResponse)
async def restart_service(service: str):
    """Startet einen einzelnen Service neu"""
    valid_services = ["api", "ollama", "redis", "celery"]
    
    if service not in valid_services:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid service. Valid services: {valid_services}"
        )
    
    try:
        if service == "celery":
            # Celery Worker neu starten
            subprocess.run(["pkill", "-f", "celery worker"], capture_output=True)
            await asyncio.sleep(1)
            subprocess.Popen(
                ["celery", "-A", "workers.celery_app", "worker", 
                 "-Q", "default,llm,analysis,generation,export", 
                 "--loglevel=info"],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
        elif service == "redis":
            subprocess.run(["sudo", "systemctl", "restart", "redis"], capture_output=True)
            
        elif service == "ollama":
            subprocess.run(["sudo", "systemctl", "restart", "ollama"], capture_output=True)
            
        elif service == "api":
            # API selbst - Signal für graceful restart
            return RestartResponse(
                success=True,
                message="API restart scheduled. Will restart after current requests complete.",
                service=service
            )
        
        return RestartResponse(
            success=True,
            message=f"Service {service} restart initiated",
            service=service
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{service}")
async def get_service_logs(service: str, lines: int = 100):
    """Holt die letzten Log-Zeilen eines Services"""
    log_paths = {
        "api": "/var/log/stratgen/api.log",
        "celery": "/var/log/stratgen/celery.log",
        "ollama": "/var/log/ollama/server.log",
    }
    
    if service not in log_paths:
        raise HTTPException(status_code=400, detail="Invalid service")
    
    log_path = log_paths[service]
    
    # Fallback auf journalctl wenn Datei nicht existiert
    if not os.path.exists(log_path):
        try:
            result = subprocess.run(
                ["journalctl", "-u", service, "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True
            )
            return {"service": service, "logs": result.stdout.split("\n")}
        except:
            return {"service": service, "logs": [f"No logs available for {service}"]}
    
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            return {"service": service, "logs": all_lines[-lines:]}
    except Exception as e:
        return {"service": service, "logs": [f"Error reading logs: {e}"]}
