"""
Sessions API - Session Management für Frontend
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path
import json

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# In-memory session storage (in Production: Redis/DB)
active_sessions: Dict[str, Dict[str, Any]] = {}

BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


class SessionConfig(BaseModel):
    company_name: str
    project_name: str
    industry: Optional[str] = "Technology"
    audience: Optional[str] = "C-Level"
    brief: str
    deck_size: int = 10
    temperature: float = 0.7
    colors: Optional[Dict[str, str]] = None
    style: Optional[str] = "corporate"


class SessionStatus(BaseModel):
    id: str
    status: str
    phase: str
    progress: float
    slides_generated: int
    total_slides: int
    created_at: str
    updated_at: str
    errors: List[str] = []


class SessionCreate(BaseModel):
    config: SessionConfig


@router.post("/create", response_model=SessionStatus)
async def create_session(data: SessionCreate):
    """Erstellt eine neue Generation Session"""
    session_id = str(uuid.uuid4())[:8]
    
    session = {
        "id": session_id,
        "config": data.config.dict(),
        "status": "created",
        "phase": "pending",
        "progress": 0.0,
        "slides_generated": 0,
        "total_slides": data.config.deck_size,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "errors": [],
        "files": [],
        "result": None
    }
    
    # Create session directory
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    (session_dir / "uploads").mkdir(exist_ok=True)
    
    # Save config
    with open(session_dir / "config.json", "w") as f:
        json.dump(session, f, indent=2)
    
    active_sessions[session_id] = session
    
    return SessionStatus(**session)


@router.get("/active", response_model=List[SessionStatus])
async def get_active_sessions():
    """Gibt alle aktiven Sessions zurück"""
    return [SessionStatus(**s) for s in active_sessions.values()]


@router.get("/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Gibt den Status einer Session zurück"""
    if session_id not in active_sessions:
        # Try to load from disk
        session_dir = SESSIONS_DIR / session_id
        if session_dir.exists():
            config_file = session_dir / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    session = json.load(f)
                    active_sessions[session_id] = session
                    return SessionStatus(**session)
        
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStatus(**active_sessions[session_id])


@router.post("/{session_id}/upload")
async def upload_to_session(session_id: str, file: UploadFile = File(...)):
    """Lädt eine Datei zu einer Session hoch"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_dir = SESSIONS_DIR / session_id / "uploads"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    target = session_dir / safe_name
    
    with open(target, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Add to session
    active_sessions[session_id]["files"].append({
        "name": safe_name,
        "size": len(content),
        "type": target.suffix
    })
    active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "filename": safe_name,
        "session_id": session_id
    }


@router.post("/{session_id}/start")
async def start_session(session_id: str):
    """Startet die Generierung für eine Session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if session["status"] == "running":
        raise HTTPException(status_code=400, detail="Session already running")
    
    # Update status
    session["status"] = "running"
    session["phase"] = "analyze"
    session["updated_at"] = datetime.now().isoformat()
    
    # In real implementation: Start async task
    # task = celery_app.send_task('workers.tasks.generation_tasks.generate_full_pipeline', 
    #                             args=[session_id, session["config"]])
    # session["task_id"] = task.id
    
    return {"success": True, "session_id": session_id, "status": "running"}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Löscht eine Session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    session_dir = SESSIONS_DIR / session_id
    if session_dir.exists():
        import shutil
        shutil.rmtree(session_dir)
    
    return {"success": True, "deleted": session_id}
