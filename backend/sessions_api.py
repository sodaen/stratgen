"""
Sessions API - Session Management für Frontend
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path
import json
import asyncio

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# In-memory session storage (in Production: Redis/DB)
active_sessions: Dict[str, Dict[str, Any]] = {}

BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


class SessionConfig(BaseModel):
    company_name: str = ""
    project_name: str = ""
    industry: Optional[str] = "Technology"
    audience: Optional[str] = "C-Level"
    brief: str = ""
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
    config: Optional[Dict[str, Any]] = None


class SessionCreate(BaseModel):
    config: SessionConfig


def update_session(session_id: str, **kwargs):
    """Update session and save to disk"""
    if session_id in active_sessions:
        active_sessions[session_id].update(kwargs)
        active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        # Save to disk
        session_dir = SESSIONS_DIR / session_id
        if session_dir.exists():
            with open(session_dir / "config.json", "w") as f:
                json.dump(active_sessions[session_id], f, indent=2)


async def run_generation(session_id: str):
    """Führt die eigentliche Generierung aus"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            return
        
        config = session.get("config", {})
        
        # Import Live Generator
        from services.live_generator import LiveGenerator
        
        generator = LiveGenerator()
        
        # Callback für Progress Updates
        def progress_callback(phase: str, progress: float, slide_num: int = 0):
            update_session(
                session_id,
                phase=phase,
                progress=progress,
                slides_generated=slide_num
            )
        
        # Generiere
        update_session(session_id, status="running", phase="analyze")
        
        result = await asyncio.to_thread(
            generator.generate_full,
            briefing=config.get("brief", ""),
            company_name=config.get("company_name", ""),
            project_name=config.get("project_name", ""),
            industry=config.get("industry", "Technology"),
            audience=config.get("audience", "C-Level"),
            deck_size=config.get("deck_size", 10),
            temperature=config.get("temperature", 0.7),
            style=config.get("style", "corporate"),
            progress_callback=progress_callback
        )
        
        # Speichere Ergebnis
        update_session(
            session_id,
            status="complete",
            phase="complete",
            progress=100.0,
            slides_generated=len(result.get("slides", [])),
            result=result
        )
        
        # Speichere Slides separat
        session_dir = SESSIONS_DIR / session_id
        with open(session_dir / "slides.json", "w") as f:
            json.dump(result.get("slides", []), f, indent=2)
            
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        update_session(
            session_id,
            status="error",
            phase="error",
            errors=[str(e)]
        )
        print(f"[Session {session_id}] Generation error: {error_msg}")


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
    # Filter nur running sessions
    running = [s for s in active_sessions.values() if s.get("status") == "running"]
    return [SessionStatus(**s) for s in running]


@router.get("/{session_id}/status")
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
                    return session
        
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]


@router.get("/{session_id}/slides")
async def get_session_slides(session_id: str):
    """Gibt die generierten Slides zurück"""
    session_dir = SESSIONS_DIR / session_id
    slides_file = session_dir / "slides.json"
    
    if slides_file.exists():
        with open(slides_file) as f:
            return {"slides": json.load(f)}
    
    # Oder aus Session
    if session_id in active_sessions:
        result = active_sessions[session_id].get("result", {})
        return {"slides": result.get("slides", [])}
    
    return {"slides": []}


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
async def start_session(session_id: str, background_tasks: BackgroundTasks):
    """Startet die Generierung für eine Session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if session["status"] == "running":
        raise HTTPException(status_code=400, detail="Session already running")
    
    # Update status
    session["status"] = "starting"
    session["phase"] = "initializing"
    session["updated_at"] = datetime.now().isoformat()
    
    # Start generation in background
    background_tasks.add_task(run_generation, session_id)
    
    return {"success": True, "session_id": session_id, "status": "starting"}


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
