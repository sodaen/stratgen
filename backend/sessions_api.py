"""
Sessions API - Session Management für Frontend
Verwendet Disk-Storage für Konsistenz über mehrere Gunicorn-Worker
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path
import json
import asyncio
import fcntl

router = APIRouter(prefix="/sessions", tags=["Sessions"])

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


class SessionCreate(BaseModel):
    config: SessionConfig


def read_session(session_id: str) -> Optional[Dict]:
    """Liest Session von Disk"""
    session_dir = SESSIONS_DIR / session_id
    config_file = session_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def write_session(session_id: str, data: Dict):
    """Schreibt Session auf Disk mit File-Locking"""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    config_file = session_dir / "config.json"
    
    with open(config_file, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(data, f, indent=2, default=str)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def update_session(session_id: str, **kwargs):
    """Update session auf Disk"""
    session = read_session(session_id)
    if session:
        session.update(kwargs)
        session["updated_at"] = datetime.now().isoformat()
        write_session(session_id, session)


def map_deck_size(size: int) -> str:
    """Mappt numerische Größe auf LiveGenerator Format"""
    if size <= 7:
        return "small"
    elif size <= 15:
        return "medium"
    else:
        return "large"


async def run_generation(session_id: str):
    """Führt die Generierung aus"""
    try:
        session = read_session(session_id)
        if not session:
            return
        
        config = session.get("config", {})
        
        # Import Live Generator
        from services.live_generator import LiveGenerator, LiveGenerationRequest
        
        generator = LiveGenerator()
        
        # Erstelle Request
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
        
        # Update Status
        update_session(session_id, generation_id=gen_id, status="running", phase="analyze")
        
        slides = []
        
        # Führe Generation aus
        async for event in generator.generate_async(gen_id):
            event_type = event.get("type", "")
            
            if event_type == "phase_start":
                phase = event.get("data", {}).get("phase", event.get("phase", ""))
                update_session(session_id, phase=phase)
                
            elif event_type == "progress":
                progress = event.get("progress", event.get("data", {}).get("progress", 0))
                update_session(session_id, progress=progress)
                
            elif event_type in ("slide_generated", "slide"):
                slide = event.get("slide", event.get("data", {}).get("slide", {}))
                if slide:
                    slides.append(slide)
                    update_session(session_id, slides_generated=len(slides))
                    
            elif event_type in ("complete", "completed"):
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
        print(f"[Session {session_id}] Generation error: {e}")
        print(traceback.format_exc())
        update_session(session_id, status="error", phase="error", errors=[str(e)])


@router.post("/create")
async def create_session(data: SessionCreate):
    """Erstellt eine neue Session"""
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
    
    write_session(session_id, session)
    
    return session


@router.get("/active")
async def get_active_sessions():
    """Gibt alle Sessions zurück (von Disk)"""
    sessions = []
    
    if SESSIONS_DIR.exists():
        for session_dir in SESSIONS_DIR.iterdir():
            if session_dir.is_dir():
                session = read_session(session_dir.name)
                if session:
                    sessions.append(session)
    
    # Sortiere nach created_at (neueste zuerst)
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limitiere auf die letzten 10
    return sessions[:10]


@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    """Gibt den Status einer Session zurück (von Disk)"""
    session = read_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/slides")
async def get_session_slides(session_id: str):
    """Gibt die Slides zurück"""
    session_dir = SESSIONS_DIR / session_id
    slides_file = session_dir / "slides.json"
    
    if slides_file.exists():
        with open(slides_file) as f:
            return {"slides": json.load(f)}
    
    session = read_session(session_id)
    if session and session.get("result"):
        return {"slides": session["result"].get("slides", [])}
    
    return {"slides": []}


@router.post("/{session_id}/upload")
async def upload_to_session(session_id: str, file: UploadFile = File(...)):
    """Lädt Datei hoch"""
    session = read_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_dir = SESSIONS_DIR / session_id / "uploads"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    target = session_dir / safe_name
    
    with open(target, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Update session
    files = session.get("files", [])
    files.append({"name": safe_name, "size": len(content), "type": target.suffix})
    update_session(session_id, files=files)
    
    return {"success": True, "filename": safe_name}


@router.post("/{session_id}/start")
async def start_session(session_id: str, background_tasks: BackgroundTasks):
    """Startet die Generierung"""
    session = read_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("status") == "running":
        raise HTTPException(status_code=400, detail="Session already running")
    
    # Update Status
    update_session(session_id, status="starting", phase="initializing")
    
    # Start im Background
    background_tasks.add_task(run_generation, session_id)
    
    return {"success": True, "session_id": session_id, "status": "starting"}


@router.put("/{session_id}/slides")
async def update_session_slides(session_id: str, data: Dict[str, Any]):
    """Aktualisiert Slides"""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    slides = data.get("slides", [])
    
    with open(session_dir / "slides.json", "w") as f:
        json.dump(slides, f, indent=2, default=str)
    
    return {"success": True, "slides_count": len(slides)}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Löscht Session"""
    session_dir = SESSIONS_DIR / session_id
    if session_dir.exists():
        import shutil
        shutil.rmtree(session_dir)
    
    return {"success": True, "deleted": session_id}
