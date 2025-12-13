# -*- coding: utf-8 -*-
"""
backend/live_generator_api.py
=============================
API Endpoints für Live Generator (Gamma.app-ähnlich)

Features:
- SSE Streaming für Live Updates
- Real-time Progress
- Slide Preview während Generierung
- Live Editing

Author: StratGen Agent V3.6
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json

router = APIRouter(prefix="/live", tags=["Live Generator"])

# ============================================
# IMPORTS
# ============================================

try:
    from services.live_generator import (
        live_generator,
        start_generation,
        get_generation_status,
        get_slide_preview,
        edit_slide,
        cancel_generation,
        get_all_slides,
        check_status as generator_status
    )
    HAS_LIVE_GENERATOR = True
except ImportError as e:
    HAS_LIVE_GENERATOR = False
    print(f"Live Generator Import Error: {e}")


# ============================================
# MODELS
# ============================================

class LiveGenerationRequest(BaseModel):
    topic: str
    brief: str
    customer_name: str = ""
    industry: str = ""
    target_audience: str = ""
    deck_size: int = 15
    enable_charts: bool = True
    enable_images: bool = False


class SlideEditRequest(BaseModel):
    slide_index: int
    field: str  # title, bullets, type
    new_value: Any
    regenerate: bool = False


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status")
def live_status():
    """Status des Live Generators."""
    if not HAS_LIVE_GENERATOR:
        return {"ok": False, "error": "Live Generator nicht verfügbar"}
    return generator_status()


@router.post("/start")
def api_start_generation(req: LiveGenerationRequest):
    """
    Startet eine neue Live-Generierung.
    
    Returns generation_id für Streaming.
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    result = start_generation({
        "topic": req.topic,
        "brief": req.brief,
        "customer_name": req.customer_name,
        "industry": req.industry,
        "deck_size": req.deck_size,
        "enable_charts": req.enable_charts,
        "enable_images": req.enable_images
    })
    
    return result


@router.get("/stream/{generation_id}")
async def api_stream_generation(generation_id: str, request: Request):
    """
    SSE Stream für Live-Updates während der Generierung.
    
    Client sollte EventSource verwenden:
    ```javascript
    const source = new EventSource('/live/stream/xxx');
    source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    ```
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    session = live_generator.get_session(generation_id)
    if not session:
        raise HTTPException(404, "Generation nicht gefunden")
    
    async def event_generator():
        """Generiert SSE Events."""
        try:
            async for event in live_generator.generate_async(generation_id):
                # Prüfe ob Client noch verbunden
                if await request.is_disconnected():
                    break
                
                # Format als SSE
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"
                
                # Kleine Pause für Streaming
                await asyncio.sleep(0.05)
            
            # Abschluss-Event
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
            
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Für nginx
        }
    )


@router.get("/progress/{generation_id}")
def api_get_progress(generation_id: str):
    """Gibt den aktuellen Fortschritt zurück (Polling-Alternative)."""
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    return get_generation_status(generation_id)


@router.get("/preview/{generation_id}/{slide_index}")
def api_get_slide_preview(generation_id: str, slide_index: int):
    """Gibt Preview eines einzelnen Slides zurück."""
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    return get_slide_preview(generation_id, slide_index)


@router.get("/slides/{generation_id}")
def api_get_all_slides(generation_id: str):
    """Gibt alle generierten Slides zurück."""
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    return get_all_slides(generation_id)


@router.post("/edit/{generation_id}")
def api_edit_slide(generation_id: str, req: SlideEditRequest):
    """
    Bearbeitet einen Slide während/nach der Generierung.
    
    Ermöglicht Live-Editing wie bei Gamma.app.
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    return edit_slide(generation_id, {
        "slide_index": req.slide_index,
        "field": req.field,
        "new_value": req.new_value,
        "regenerate": req.regenerate
    })


@router.post("/cancel/{generation_id}")
def api_cancel_generation(generation_id: str):
    """Bricht eine laufende Generierung ab."""
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    return cancel_generation(generation_id)


@router.post("/regenerate/{generation_id}/{slide_index}")
def api_regenerate_slide(generation_id: str, slide_index: int):
    """
    Regeneriert einen einzelnen Slide.
    
    Nützlich wenn der User mit einem Slide nicht zufrieden ist.
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    # TODO: Implementiere Slide-Regenerierung
    return {"ok": False, "error": "Nicht implementiert"}


@router.post("/export/{generation_id}")
def api_export_generation(generation_id: str, format: str = "pptx"):
    """
    Exportiert das generierte Deck.
    
    Formate: pptx, html, pdf, json
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    session = live_generator.get_session(generation_id)
    if not session:
        raise HTTPException(404, "Generation nicht gefunden")
    
    slides = session.completed_slides
    
    if not slides:
        raise HTTPException(400, "Keine Slides generiert")
    
    # Export durchführen
    try:
        if format == "json":
            return {"ok": True, "slides": slides}
        
        elif format == "html":
            from services.multimodal_export import export_to_html
            result = export_to_html(slides, session.request.topic)
            return result
        
        elif format == "pptx":
            # PowerPoint mit PPTXDesignerV2
            from services.pptx_designer_v2 import PPTXDesignerV2
            
            colors = {
                "primary": "#1E40AF",
                "secondary": "#3B82F6",
                "accent": "#10B981",
                "background": "#FFFFFF",
                "text": "#111827"
            }
            
            designer = PPTXDesignerV2(colors=colors)
            pptx_bytes = designer.create_presentation(
                slides=slides,
                title=session.request.topic,
                company=session.request.customer_name or "",
                include_sources_slide=True
            )
            
            # Speichern
            import time
            from pathlib import Path
            ts = int(time.time())
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            filename = f"live-{generation_id[:8]}-{ts}.pptx"
            out_path = exports_dir / filename
            
            with open(out_path, "wb") as f:
                f.write(pptx_bytes)
            
            result = {
                "ok": True,
                "url": f"/exports/download/{filename}",
                "path": str(out_path),
                "slides_count": len(slides)
            }
            return result
        else:
            return {"ok": False, "error": f"Unbekanntes Format: {format}"}
    
    except ImportError as e:
        return {"ok": False, "error": f"Export-Modul nicht verfügbar: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================
# WEBSOCKET (für zukünftige Implementierung)
# ============================================

# @router.websocket("/ws/{generation_id}")
# async def websocket_stream(websocket: WebSocket, generation_id: str):
#     """
#     WebSocket Alternative zu SSE.
#     Ermöglicht bidirektionale Kommunikation.
#     """
#     await websocket.accept()
#     
#     try:
#         async for event in live_generator.generate_async(generation_id):
#             await websocket.send_json(event)
#     except WebSocketDisconnect:
#         pass


# ============================================
# SYNCHRONER GENERATE ENDPOINT (für Tests)
# ============================================

@router.post("/generate-sync")
async def api_generate_sync(req: LiveGenerationRequest):
    """
    Synchrone Generierung - wartet bis alle Slides fertig sind.
    Für Backend-Tests und CLI-Nutzung.
    
    ACHTUNG: Kann bei vielen Slides mehrere Minuten dauern!
    """
    if not HAS_LIVE_GENERATOR:
        raise HTTPException(500, "Live Generator nicht verfügbar")
    
    import time
    start_time = time.time()
    
    # Session erstellen
    result = start_generation({
        "topic": req.topic,
        "brief": req.brief,
        "customer_name": req.customer_name,
        "industry": req.industry,
        "target_audience": req.target_audience,
        "deck_size": req.deck_size,
        "style": req.style,
        "enable_charts": req.enable_charts,
        "enable_images": req.enable_images,
        "temperature": req.temperature
    })
    
    if not result.get("ok", True):
        return result
    
    generation_id = result.get("generation_id")
    if not generation_id:
        return {"ok": False, "error": "No generation_id"}
    
    # Generierung durchführen
    slides = []
    events = []
    error = None
    
    try:
        async for event in live_generator.generate_async(generation_id):
            events.append(event)
            
            if event.get("type") == "slide_ready":
                slide = event.get("data", {}).get("slide", {})
                slides.append(slide)
                # Log progress
                print(f"[{generation_id}] Slide {len(slides)} generiert: {slide.get('title', '?')}")
            
            elif event.get("type") == "error":
                error = event.get("data", {}).get("message", "Unknown error")
                break
            
            elif event.get("type") == "complete":
                break
    
    except Exception as e:
        error = str(e)
    
    duration = time.time() - start_time
    
    if error:
        return {
            "ok": False,
            "error": error,
            "generation_id": generation_id,
            "slides_generated": len(slides),
            "duration_seconds": round(duration, 1)
        }
    
    # Session-Daten speichern für späteren Export
    session = live_generator.get_session(generation_id)
    if session:
        # Speichere als JSON für Export
        import json
        from pathlib import Path
        
        session_file = Path("data/live_sessions") / f"{generation_id}.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump({
                "generation_id": generation_id,
                "title": req.topic,
                "slides": slides,
                "request": {
                    "topic": req.topic,
                    "brief": req.brief,
                    "customer_name": req.customer_name,
                    "deck_size": req.deck_size
                },
                "duration_seconds": round(duration, 1)
            }, f, indent=2, ensure_ascii=False)
    
    return {
        "ok": True,
        "generation_id": generation_id,
        "slides_count": len(slides),
        "duration_seconds": round(duration, 1),
        "slides_per_minute": round(len(slides) / (duration / 60), 1) if duration > 0 else 0,
        "export_url": f"/api/export/pptx/{generation_id}",
        "slides": slides
    }
