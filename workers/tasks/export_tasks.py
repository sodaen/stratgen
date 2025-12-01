# -*- coding: utf-8 -*-
"""
workers/tasks/export_tasks.py
=============================
Export Tasks für Celery Worker

Tasks für PPTX, PDF, HTML Export.

Tasks:
- export_pptx: PowerPoint Export
- export_pdf: PDF Export
- export_html: HTML Export
- export_multi: Multi-Format Export
"""
from celery import shared_task
from typing import Dict, Any, List, Optional
import time
import os
from pathlib import Path

# ============================================
# IMPORTS
# ============================================

def get_pptx_builder():
    try:
        from services.pptx_builder import build_pptx
        return build_pptx
    except ImportError:
        return None

def get_multimodal_export():
    try:
        from services.multimodal_export import (
            export_to_html,
            export_to_pdf,
            export_to_markdown,
            export_to_json
        )
        return {
            "html": export_to_html,
            "pdf": export_to_pdf,
            "markdown": export_to_markdown,
            "json": export_to_json
        }
    except ImportError:
        return {}


# ============================================
# CONFIGURATION
# ============================================

EXPORT_DIR = Path(os.getenv("STRATGEN_EXPORT_DIR", "data/exports"))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# TASKS
# ============================================

@shared_task(
    bind=True,
    name="export.pptx",
    max_retries=2,
    time_limit=120
)
def export_pptx(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    template_path: Optional[str] = None,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als PowerPoint.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        template_path: Optionaler Template-Pfad
        output_filename: Optionaler Dateiname
    
    Returns:
        Dictionary mit Pfad zur PPTX
    """
    build_pptx = get_pptx_builder()
    
    if build_pptx is None:
        return {"ok": False, "error": "PPTX Builder nicht verfügbar"}
    
    start_time = time.time()
    
    try:
        # Dateiname generieren
        if not output_filename:
            timestamp = int(time.time())
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
            output_filename = f"{safe_title}_{timestamp}.pptx"
        
        output_path = EXPORT_DIR / output_filename
        
        result = build_pptx(
            slides=slides,
            title=title,
            template_path=template_path,
            output_path=str(output_path)
        )
        
        elapsed = time.time() - start_time
        
        if result.get("ok"):
            return {
                "ok": True,
                "path": str(output_path),
                "filename": output_filename,
                "size_bytes": output_path.stat().st_size if output_path.exists() else 0,
                "elapsed_ms": int(elapsed * 1000),
                "task_id": self.request.id
            }
        else:
            return {
                "ok": False,
                "error": result.get("error", "Export failed"),
                "task_id": self.request.id
            }
            
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="export.html",
    max_retries=2,
    time_limit=60
)
def export_html(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als HTML.
    """
    exporters = get_multimodal_export()
    export_to_html = exporters.get("html")
    
    if export_to_html is None:
        return {"ok": False, "error": "HTML Exporter nicht verfügbar"}
    
    start_time = time.time()
    
    try:
        if not output_filename:
            timestamp = int(time.time())
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
            output_filename = f"{safe_title}_{timestamp}.html"
        
        output_path = EXPORT_DIR / output_filename
        
        result = export_to_html(slides, title, str(output_path))
        
        elapsed = time.time() - start_time
        
        return {
            "ok": result.get("ok", False),
            "path": str(output_path) if result.get("ok") else None,
            "filename": output_filename,
            "elapsed_ms": int(elapsed * 1000),
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="export.pdf",
    max_retries=2,
    time_limit=120
)
def export_pdf(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als PDF.
    """
    exporters = get_multimodal_export()
    export_to_pdf = exporters.get("pdf")
    
    if export_to_pdf is None:
        return {"ok": False, "error": "PDF Exporter nicht verfügbar"}
    
    start_time = time.time()
    
    try:
        if not output_filename:
            timestamp = int(time.time())
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
            output_filename = f"{safe_title}_{timestamp}.pdf"
        
        output_path = EXPORT_DIR / output_filename
        
        result = export_to_pdf(slides, title, str(output_path))
        
        elapsed = time.time() - start_time
        
        return {
            "ok": result.get("ok", False),
            "path": str(output_path) if result.get("ok") else None,
            "filename": output_filename,
            "elapsed_ms": int(elapsed * 1000),
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="export.markdown",
    max_retries=2,
    time_limit=30
)
def export_markdown(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als Markdown.
    """
    exporters = get_multimodal_export()
    export_to_md = exporters.get("markdown")
    
    if export_to_md is None:
        # Fallback: Einfacher Markdown Export
        try:
            if not output_filename:
                timestamp = int(time.time())
                safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
                output_filename = f"{safe_title}_{timestamp}.md"
            
            output_path = EXPORT_DIR / output_filename
            
            md_content = f"# {title}\n\n"
            for i, slide in enumerate(slides):
                md_content += f"## Slide {i + 1}: {slide.get('title', '')}\n\n"
                for bullet in slide.get("bullets", []):
                    md_content += f"- {bullet}\n"
                md_content += "\n"
            
            output_path.write_text(md_content, encoding="utf-8")
            
            return {
                "ok": True,
                "path": str(output_path),
                "filename": output_filename,
                "task_id": self.request.id
            }
            
        except Exception as e:
            return {"ok": False, "error": str(e), "task_id": self.request.id}
    
    # Nutze Service wenn verfügbar
    try:
        if not output_filename:
            timestamp = int(time.time())
            output_filename = f"{title[:30]}_{timestamp}.md"
        
        output_path = EXPORT_DIR / output_filename
        result = export_to_md(slides, title, str(output_path))
        
        return {
            "ok": result.get("ok", False),
            "path": str(output_path),
            "filename": output_filename,
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="export.json",
    max_retries=1,
    time_limit=30
)
def export_json(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    metadata: Optional[Dict[str, Any]] = None,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als JSON.
    """
    import json
    
    try:
        if not output_filename:
            timestamp = int(time.time())
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
            output_filename = f"{safe_title}_{timestamp}.json"
        
        output_path = EXPORT_DIR / output_filename
        
        export_data = {
            "title": title,
            "slides": slides,
            "metadata": metadata or {},
            "exported_at": time.time(),
            "version": "3.8"
        }
        
        output_path.write_text(
            json.dumps(export_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return {
            "ok": True,
            "path": str(output_path),
            "filename": output_filename,
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "task_id": self.request.id}


@shared_task(
    bind=True,
    name="export.multi",
    max_retries=1,
    time_limit=300
)
def export_multi(
    self,
    slides: List[Dict[str, Any]],
    title: str,
    formats: List[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Exportiert in mehrere Formate gleichzeitig.
    
    Args:
        slides: Die Slides
        title: Titel
        formats: Liste der Formate (pptx, html, pdf, markdown, json)
        metadata: Optionale Metadaten
    
    Returns:
        Dictionary mit Pfaden zu allen Exports
    """
    if formats is None:
        formats = ["pptx", "json"]
    
    results = {}
    errors = []
    
    for fmt in formats:
        try:
            if fmt == "pptx":
                result = export_pptx(slides, title)
            elif fmt == "html":
                result = export_html(slides, title)
            elif fmt == "pdf":
                result = export_pdf(slides, title)
            elif fmt == "markdown":
                result = export_markdown(slides, title)
            elif fmt == "json":
                result = export_json(slides, title, metadata)
            else:
                result = {"ok": False, "error": f"Unbekanntes Format: {fmt}"}
            
            results[fmt] = result
            
            if not result.get("ok"):
                errors.append(f"{fmt}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            errors.append(f"{fmt}: {str(e)}")
            results[fmt] = {"ok": False, "error": str(e)}
    
    successful = sum(1 for r in results.values() if r.get("ok"))
    
    return {
        "ok": successful > 0,
        "exports": results,
        "successful": successful,
        "total": len(formats),
        "errors": errors,
        "task_id": self.request.id
    }


# ============================================
# HELPER TASKS
# ============================================

@shared_task(name="export.cleanup_old")
def cleanup_old_exports(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Löscht alte Export-Dateien.
    """
    import time
    
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    
    deleted = 0
    
    for f in EXPORT_DIR.glob("*"):
        if f.is_file():
            age = now - f.stat().st_mtime
            if age > max_age_seconds:
                try:
                    f.unlink()
                    deleted += 1
                except Exception:
                    pass
    
    return {
        "ok": True,
        "deleted_files": deleted,
        "export_dir": str(EXPORT_DIR)
    }


@shared_task(name="export.list_exports")
def list_exports() -> Dict[str, Any]:
    """
    Listet alle Export-Dateien.
    """
    exports = []
    
    for f in EXPORT_DIR.glob("*"):
        if f.is_file():
            exports.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime,
                "format": f.suffix[1:] if f.suffix else "unknown"
            })
    
    exports.sort(key=lambda x: x["modified"], reverse=True)
    
    return {
        "ok": True,
        "exports": exports[:50],  # Max 50
        "total": len(exports),
        "export_dir": str(EXPORT_DIR)
    }
