"""
Generator v2 API für Stratgen.
Endpoints für Content-Generierung und Export mit Quellen.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

router = APIRouter(prefix="/generator/v2", tags=["generator-v2"])
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    topic: str
    brief: str = ""
    industry: str = ""
    customer: str = ""
    keywords: List[str] = []
    min_slides: int = 3
    max_slides: int = 10
    colors: Optional[Dict[str, str]] = None
    palette: str = "corporate"


class ExportRequest(BaseModel):
    slides: List[Dict]
    title: str = "Präsentation"
    company: str = ""
    colors: Optional[Dict[str, str]] = None
    palette: str = "corporate"
    include_sources: bool = True
    filename: Optional[str] = None


@router.post("/generate")
async def generate_presentation(req: GenerateRequest):
    """
    Generiert Präsentationsinhalt mit RAG und externen Quellen.
    
    Features:
    - Dynamische Slide-Anzahl basierend auf Komplexität
    - RAG-basiertes Wissen
    - Wikipedia, News Integration
    - Automatische Quellenerfassung
    """
    try:
        from services.content_generator_v2 import generate_presentation
        
        slides, metadata = generate_presentation(
            topic=req.topic,
            brief=req.brief,
            industry=req.industry,
            customer=req.customer,
            keywords=req.keywords,
            config={"colors": req.colors, "palette": req.palette}
        )
        
        return {
            "ok": True,
            "slides": slides,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/pptx")
async def export_pptx(req: ExportRequest):
    """
    Exportiert Slides zu PPTX mit Quellen.
    
    Features:
    - Wizard-Farben
    - Quellen-Footer auf jedem Slide
    - Quellenübersicht am Ende
    - Seitenzahlen
    """
    try:
        from services.export_service_v2 import export_to_pptx
        
        result = export_to_pptx(
            slides=req.slides,
            title=req.title,
            company=req.company,
            colors=req.colors,
            palette=req.palette,
            include_sources=req.include_sources,
            filename=req.filename
        )
        
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/json")
async def export_json(req: ExportRequest):
    """Exportiert Slides als JSON."""
    try:
        from services.export_service_v2 import export_to_json
        
        result = export_to_json(
            slides=req.slides,
            metadata={"title": req.title, "company": req.company},
            filename=req.filename
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports")
async def list_exports(limit: int = 20):
    """Listet letzte Exports."""
    from services.export_service_v2 import get_export_history
    return {"ok": True, "exports": get_export_history(limit)}


@router.get("/sources/status")
async def sources_status():
    """Status der Datenquellen."""
    try:
        from services.data_services import check_data_services
        return {"ok": True, "services": check_data_services()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
