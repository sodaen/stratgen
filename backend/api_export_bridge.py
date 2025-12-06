"""
API Export Bridge - Verbindet Frontend mit Export-Services.
Frontend ruft: /api/export/{format}/{session_id}
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import time

router = APIRouter(prefix="/api", tags=["export-bridge"])

EXPORTS_DIR = Path("data/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/export/{format}/{session_id}")
@router.post("/export/{format}/{session_id}")
async def export_session(format: str, session_id: str):
    """
    Exportiert eine Session zu PPTX/PDF/etc.
    Wird vom Frontend (Editor, Generator) aufgerufen.
    """
    
    if format not in ["pptx", "pdf", "json", "md"]:
        raise HTTPException(400, f"Unsupported format: {format}")
    
    # 1. Versuche Session-Daten zu laden
    session_file = Path(f"data/sessions/{session_id}.json")
    slides = []
    title = "Strategie Präsentation"
    colors = None
    
    if session_file.exists():
        try:
            with open(session_file) as f:
                session_data = json.load(f)
            slides = session_data.get("slides", [])
            title = session_data.get("title", title)
            colors = session_data.get("colors")
        except:
            pass
    
    # 2. Versuche aus Live-Generator Session
    if not slides:
        live_session_file = Path(f"data/live_sessions/{session_id}.json")
        if live_session_file.exists():
            try:
                with open(live_session_file) as f:
                    live_data = json.load(f)
                slides = live_data.get("slides", [])
                title = live_data.get("request", {}).get("topic", title)
                colors = live_data.get("request", {}).get("colors")
            except:
                pass
    
    # 3. Versuche aus Project
    if not slides:
        try:
            import httpx
            resp = httpx.get(f"http://127.0.0.1:8011/projects/{session_id}", timeout=5)
            if resp.status_code == 200:
                proj_data = resp.json()
                if proj_data.get("ok"):
                    project = proj_data.get("project", {})
                    meta = project.get("meta", {})
                    slides = meta.get("slide_plan", [])
                    title = project.get("topic", title)
        except:
            pass
    
    if not slides:
        raise HTTPException(404, f"No slides found for session: {session_id}")
    
    # 4. Export durchführen
    if format == "pptx":
        try:
            from services.pptx_designer_v2 import PPTXDesignerV2
            
            designer = PPTXDesignerV2(colors=colors)
            
            # Erstelle PPTX
            ts = int(time.time())
            filename = f"export-{session_id[:8]}-{ts}.pptx"
            out_path = EXPORTS_DIR / filename
            
            designer.create_presentation(
                slides=slides,
                title=title,
                output_path=str(out_path)
            )
            
            return {
                "ok": True,
                "url": f"/exports/download/{filename}",
                "path": str(out_path),
                "slides_count": len(slides)
            }
            
        except ImportError:
            # Fallback zu einfachem PPTX
            try:
                from pptx import Presentation
                from pptx.util import Inches, Pt
                
                prs = Presentation()
                
                for slide_data in slides[:100]:
                    slide_title = slide_data.get("title", "Slide")
                    bullets = slide_data.get("bullets", [])
                    content = slide_data.get("content", "")
                    
                    layout = prs.slide_layouts[1]  # Title and Content
                    slide = prs.slides.add_slide(layout)
                    
                    # Titel setzen
                    if slide.shapes.title:
                        slide.shapes.title.text = slide_title
                    
                    # Content/Bullets
                    if bullets or content:
                        try:
                            body = slide.shapes.placeholders[1].text_frame
                            body.clear()
                            
                            if bullets:
                                body.text = str(bullets[0]) if bullets else ""
                                for b in bullets[1:]:
                                    p = body.add_paragraph()
                                    p.text = str(b)
                            elif content:
                                body.text = content
                        except:
                            pass
                
                ts = int(time.time())
                filename = f"export-{session_id[:8]}-{ts}.pptx"
                out_path = EXPORTS_DIR / filename
                prs.save(str(out_path))
                
                return {
                    "ok": True,
                    "url": f"/exports/download/{filename}",
                    "path": str(out_path),
                    "slides_count": len(slides)
                }
                
            except Exception as e:
                raise HTTPException(500, f"PPTX export failed: {str(e)}")
    
    elif format == "json":
        ts = int(time.time())
        filename = f"export-{session_id[:8]}-{ts}.json"
        out_path = EXPORTS_DIR / filename
        
        with open(out_path, 'w') as f:
            json.dump({"title": title, "slides": slides}, f, indent=2, ensure_ascii=False)
        
        return {
            "ok": True,
            "url": f"/exports/download/{filename}",
            "slides_count": len(slides)
        }
    
    elif format == "md":
        ts = int(time.time())
        filename = f"export-{session_id[:8]}-{ts}.md"
        out_path = EXPORTS_DIR / filename
        
        md_content = f"# {title}\n\n"
        for i, slide in enumerate(slides, 1):
            md_content += f"## Slide {i}: {slide.get('title', 'Untitled')}\n\n"
            if slide.get('content'):
                md_content += f"{slide['content']}\n\n"
            if slide.get('bullets'):
                for b in slide['bullets']:
                    md_content += f"- {b}\n"
                md_content += "\n"
        
        with open(out_path, 'w') as f:
            f.write(md_content)
        
        return {
            "ok": True,
            "url": f"/exports/download/{filename}",
            "slides_count": len(slides)
        }
    
    raise HTTPException(400, f"Format {format} not implemented")
