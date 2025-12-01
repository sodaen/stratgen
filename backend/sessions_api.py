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

# In-memory session storage
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
        
        session_dir = SESSIONS_DIR / session_id
        if session_dir.exists():
            with open(session_dir / "config.json", "w") as f:
                json.dump(active_sessions[session_id], f, indent=2, default=str)


def map_deck_size(size: int) -> str:
    """Mappt numerische Größe auf LiveGenerator Format"""
    if size <= 7:
        return "small"
    elif size <= 15:
        return "medium"
    else:
        return "large"


async def run_generation(session_id: str):
    """Führt die eigentliche Generierung aus"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            return
        
        config = session.get("config", {})
        
        # Import Live Generator
        from services.live_generator import LiveGenerator, LiveGenerationRequest
        
        generator = LiveGenerator()
        
        # Erstelle Request mit korrekten Feldern
        request = LiveGenerationRequest(
            topic=config.get("project_name", "Presentation"),
            brief=config.get("brief", ""),
            customer_name=config.get("company_name", ""),
            industry=config.get("industry", "Technology"),
            deck_size=map_deck_size(config.get("deck_size", 10)),
            style_profile=config.get("style", "corporate"),
            enable_charts=True,
            enable_images=False,
            language="de"
        )
        
        # Erstelle Generator Session
        gen_id = generator.create_session(request)
        
        # Speichere Generator ID
        update_session(session_id, generation_id=gen_id, status="running", phase="analyze")
        
        slides = []
        
        # Führe Generation aus und sammle Events
        async for event in generator.generate_async(gen_id):
            event_type = event.get("type", "")
            
            if event_type == "phase_start":
                phase = event.get("data", {}).get("phase", event.get("phase", ""))
                update_session(session_id, phase=phase)
                
            elif event_type == "progress":
                progress = event.get("progress", event.get("data", {}).get("progress", 0))
                update_session(session_id, progress=progress)
                
            elif event_type == "slide_generated" or event_type == "slide":
                slide = event.get("slide", event.get("data", {}).get("slide", {}))
                if slide:
                    slides.append(slide)
                    update_session(session_id, slides_generated=len(slides))
                    
            elif event_type == "complete" or event_type == "completed":
                final_slides = event.get("slides", event.get("data", {}).get("slides", slides))
                if final_slides:
                    slides = final_slides
                break
                
            elif event_type == "error":
                error = event.get("message", event.get("error", "Unknown error"))
                update_session(session_id, status="error", errors=[error])
                return
        
        # Speichere Ergebnis
        update_session(
            session_id,
            status="complete",
            phase="complete",
            progress=100.0,
            slides_generated=len(slides),
            result={"slides": slides}
        )
        
        # Speichere Slides separat
        session_dir = SESSIONS_DIR / session_id
        with open(session_dir / "slides.json", "w") as f:
            json.dump(slides, f, indent=2, default=str)
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[Session {session_id}] Generation error: {error_msg}")
        print(traceback.format_exc())
        update_session(
            session_id,
            status="error",
            phase="error",
            errors=[error_msg]
        )


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
    
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    (session_dir / "uploads").mkdir(exist_ok=True)
    
    with open(session_dir / "config.json", "w") as f:
        json.dump(session, f, indent=2)
    
    active_sessions[session_id] = session
    
    return SessionStatus(**session)


@router.get("/active")
async def get_active_sessions():
    """Gibt alle aktiven Sessions zurück"""
    return list(active_sessions.values())


@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    """Gibt den Status einer Session zurück"""
    if session_id not in active_sessions:
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
    
    if session_id in active_sessions:
        result = active_sessions[session_id].get("result", {})
        if result:
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
    
    active_sessions[session_id]["files"].append({
        "name": safe_name,
        "size": len(content),
        "type": target.suffix
    })
    active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
    
    return {"success": True, "filename": safe_name, "session_id": session_id}


@router.post("/{session_id}/start")
async def start_session(session_id: str, background_tasks: BackgroundTasks):
    """Startet die Generierung für eine Session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    if session["status"] == "running":
        raise HTTPException(status_code=400, detail="Session already running")
    
    session["status"] = "starting"
    session["phase"] = "initializing"
    session["updated_at"] = datetime.now().isoformat()
    
    background_tasks.add_task(run_generation, session_id)
    
    return {"success": True, "session_id": session_id, "status": "starting"}


@router.put("/{session_id}/slides")
async def update_session_slides(session_id: str, data: Dict[str, Any]):
    """Aktualisiert die Slides einer Session"""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    slides = data.get("slides", [])
    
    with open(session_dir / "slides.json", "w") as f:
        json.dump(slides, f, indent=2, default=str)
    
    if session_id in active_sessions:
        if active_sessions[session_id].get("result"):
            active_sessions[session_id]["result"]["slides"] = slides
        else:
            active_sessions[session_id]["result"] = {"slides": slides}
    
    return {"success": True, "slides_count": len(slides)}


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
