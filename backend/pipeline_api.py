from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.outline import suggest_agenda as _suggest_agenda
from services.rag_pipeline import generate_bullets_for

class AgendaItem(BaseModel):
    topic: str
    subtopics: list[str] = []

class ComposeRequest(BaseModel):
    customer_name: str
    project_title: str
    brief: dict[str, str] = {}
    mode: str = "facts"
    min_slides: int = 12
    dry_run: bool = True
    outline: Optional[list[AgendaItem]] = None

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/compose")
def compose(req: ComposeRequest):
    # 1) Agenda beschaffen
    agenda = req.outline
    if not agenda or len(agenda) == 0:
        # Fallback: sehr kleine Agenda – oder nutze LLM, wenn gewünscht:
        agenda = [AgendaItem(topic="Einführung", subtopics=["Kernaussagen"])]

    # 2) Content-Map füllen
    content_map = {}
    brief = {
        "customer_name": req.customer_name,
        **(req.brief or {}),
    }
    for item in agenda:
        topic = item.topic
        content_map.setdefault(topic, {})
        subs = item.subtopics or [""]
        for sub in subs:
            data = generate_bullets_for(topic, sub, brief, mode=req.mode)
            # Absicherung auf erwartete Struktur
            bullets = data.get("bullets", []) if isinstance(data, dict) else []
            citations = data.get("citations", []) if isinstance(data, dict) else []
            content_map[topic][sub] = {
                "bullets": bullets,
                "citations": citations
            }

    # 3) Dry-Run liefert rohe Daten zurück (Renderer folgt als nächster Schritt)
    # Optionaler Render-Zweig (nur wenn dry_run=False)
    file_name = None
    if not req.dry_run:
        payload = {
            "customer_name": req.customer_name,
            "project_title": req.project_title,
            "agenda": [i.model_dump() for i in agenda],
            "content_map": content_map
        }
        try:
            with httpx.Client(timeout=120.0) as cli:
                r = cli.post("http://127.0.0.1:8000/dev/render", json=payload)
            r.raise_for_status()
            resp = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
            file_name = (resp.get("file") or resp.get("path")) if isinstance(resp, dict) else None
            if not file_name:
                from pathlib import Path as _P
                exp = _P("export")
                if exp.exists():
                    cand = sorted(exp.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if cand:
                        file_name = cand[0].name
        except Exception as e:
            # Wir lassen Fehler in /dev/render nicht craschen, sondern liefern weiterhin Daten zurück
            pass

    return {
        "ok": True,
        "agenda": [i.model_dump() for i in agenda],
        "content_map": content_map,
        "file": file_name
    }

    # 2) Content-Map füllen
    content_map = {}
    brief = {
        "customer_name": req.customer_name,
        **(req.brief or {}),
    }
    for item in agenda:
        topic = item.topic
        content_map.setdefault(topic, {})
        subs = item.subtopics or [""]
        for sub in subs:
            data = generate_bullets_for(topic, sub, brief, mode=req.mode)
            # Absicherung auf erwartete Struktur
            bullets = data.get("bullets", []) if isinstance(data, dict) else []
            citations = data.get("citations", []) if isinstance(data, dict) else []
            content_map[topic][sub] = {
                "bullets": bullets,
                "citations": citations
            }

    # 3) Dry-Run liefert rohe Daten zurück (Renderer folgt als nächster Schritt)
    return {
        "ok": True,
        "agenda": [i.model_dump() for i in agenda],
        "content_map": content_map
    }