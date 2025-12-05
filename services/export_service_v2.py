"""
Export Service v2 für Stratgen.
Exportiert Präsentationen mit:
- PPTX Designer v2 (Wizard-Farben)
- Quellenangaben auf jedem Slide
- Quellenübersicht am Ende
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
EXPORTS_DIR = DATA_ROOT / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def export_to_pptx(slides: List[Dict],
                   title: str = "Präsentation",
                   company: str = "",
                   colors: Dict[str, str] = None,
                   palette: str = "corporate",
                   include_sources: bool = True,
                   filename: str = None) -> Dict[str, Any]:
    """
    Exportiert Slides zu PPTX mit Designer v2.
    
    Args:
        slides: Liste von Slide-Dicts mit type, title, content, sources
        title: Präsentationstitel
        company: Firmenname
        colors: Wizard-Farben (primary, secondary, accent, background, text)
        palette: Fallback-Palette
        include_sources: Quellenübersicht am Ende
        filename: Optionaler Dateiname (sonst auto-generiert)
    
    Returns:
        Dict mit Pfad, Größe, etc.
    """
    try:
        from services.pptx_designer_v2 import create_presentation_v2
        
        # Generiere PPTX
        pptx_bytes = create_presentation_v2(
            slides=slides,
            title=title,
            company=company,
            colors=colors,
            palette=palette,
            include_sources=include_sources
        )
        
        # Dateiname
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:30]
            filename = f"{safe_title}_{timestamp}.pptx"
        
        if not filename.endswith('.pptx'):
            filename += '.pptx'
        
        # Speichere
        filepath = EXPORTS_DIR / filename
        filepath.write_bytes(pptx_bytes)
        
        # Sammle Quellen für Log
        all_sources = []
        for slide in slides:
            all_sources.extend(slide.get('sources', []))
        unique_sources = list(set(all_sources))
        
        # Log Event
        _log_export_event(filepath, len(slides), len(unique_sources))
        
        return {
            "ok": True,
            "path": str(filepath),
            "filename": filename,
            "size_bytes": len(pptx_bytes),
            "slides_count": len(slides),
            "sources_count": len(unique_sources),
            "sources": unique_sources[:10]  # Top 10 für Response
        }
        
    except Exception as e:
        logger.error(f"PPTX export failed: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


def export_to_json(slides: List[Dict],
                   metadata: Dict = None,
                   filename: str = None) -> Dict[str, Any]:
    """Exportiert Slides als JSON (für Debugging/Archivierung)."""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"presentation_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = EXPORTS_DIR / filename
        
        data = {
            "slides": slides,
            "metadata": metadata or {},
            "exported_at": datetime.now().isoformat()
        }
        
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        
        return {
            "ok": True,
            "path": str(filepath),
            "filename": filename
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _log_export_event(filepath: Path, slides_count: int, sources_count: int):
    """Loggt Export-Event für Analytics."""
    try:
        import httpx
        httpx.post(
            "http://localhost:8011/admin/metrics/generation/log",
            json={
                "session_id": filepath.stem,
                "event_type": "export",
                "slides_count": slides_count,
                "quality_score": sources_count * 10  # Mehr Quellen = höhere Qualität
            },
            timeout=2.0
        )
    except:
        pass


def get_export_history(limit: int = 20) -> List[Dict]:
    """Gibt Liste der letzten Exports zurück."""
    exports = []
    
    for f in sorted(EXPORTS_DIR.glob("*.pptx"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        exports.append({
            "filename": f.name,
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return exports
