# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/footnotes", tags=["footnotes"])

class Slide(BaseModel):
    id: str
    text: str

class Source(BaseModel):
    id: str
    title: str
    url: str

class AttachReq(BaseModel):
    # Neu: tolerant – entweder slides+sources ODER nur project_id
    project_id: Optional[str] = None
    slides: Optional[List[Slide]] = None
    sources: Optional[List[Source]] = None

@router.post("/attach")
def attach_footnotes(req: AttachReq = Body(...)):
    slides = req.slides
    sources = req.sources

    # Falls nur project_id kommt, versuche Slides & Sources aus dem Projekt abzuleiten
    if (not slides or not sources) and req.project_id:
        try:
            from backend.utils_projects import load_project
            pj = load_project(req.project_id)

            # Slides aus slide_plan oder outline
            if not slides:
                slides = []
                meta = pj.get("meta") or {}
                sp = (meta.get("slide_plan") or [])
                if sp:
                    for i, it in enumerate(sp):
                        title = it.get("title") or it.get("topic") or f"Slide {i+1}"
                        slides.append(Slide(id=str(i+1), text=title))
                else:
                    outline = pj.get("outline") or {}
                    secs = outline.get("sections") or []
                    for i, sec in enumerate(secs):
                        title = (sec.get("title") or sec.get("topic") or f"Section {i+1}")
                        slides.append(Slide(id=str(i+1), text=title))

            # Sources aus content_map.*.*.citations (unique nach label+url)
            if not sources:
                uniq, out = set(), []
                cm = pj.get("content_map") or {}
                if isinstance(cm, dict):
                    for _topic, sub in cm.items():
                        if isinstance(sub, dict):
                            for _sub, obj in sub.items():
                                for c in (obj.get("citations") or []):
                                    label = c.get("label") or c.get("title") or "Quelle"
                                    url = c.get("url") or c.get("href") or ""
                                    key = (label, url)
                                    if key not in uniq:
                                        uniq.add(key)
                                        out.append(Source(id=str(len(out)+1), title=label, url=url))
                sources = out
        except Exception:
            # tolerant – auf Fehlern nicht scheitern
            pass

    slides = slides or []
    sources = sources or []

    out: List[Dict[str, Any]] = []
    for idx, sl in enumerate(slides):
        refs: List[Dict[str, str]] = []
        if idx < len(sources):
            s = sources[idx]
            refs.append({"label": s.title, "url": s.url})
        out.append({"id": sl.id, "text": sl.text, "footnotes": refs})

    return {"ok": True, "slides": out, "num_slides": len(out), "num_sources": len(sources)}
