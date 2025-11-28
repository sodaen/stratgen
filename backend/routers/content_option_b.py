from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.schemas.content import PreviewRequest, PreviewResponse, CitationRef, PreviewDiagnostics

router = APIRouter(prefix="/content", tags=["content"])

# Optionaler Hook: falls es bereits eine Projekt-/Retrieval-API gibt, hier importieren
def _try_preview_logic(project_id: str) -> PreviewResponse:
    # TODO: Hier echte Retrieval-/Compose-Logik verdrahten (RAG, rerank, dedup, passage spans)
    # Fallback liefert sinnvolle minimale Struktur, damit Frontend nicht bricht.
    outline = {"title": "Auto-Preview", "sections": [
        {"title": "Einleitung", "bullets": ["Zielsetzung", "Kontext"]},
        {"title": "Kernpunkte", "bullets": ["These A", "These B", "These C"]},
    ]}
    citations = []  # später: echte refs mit doc_id/chunk_idx/span
    diag = PreviewDiagnostics(citations_count=len(citations), retrieval_k=6, rerank_enabled=False, dedup_count=0)
    return PreviewResponse(outline=outline, bullets=None, citations=citations, diagnostics=diag)

@router.post("/preview", response_model=PreviewResponse)
def preview(req: PreviewRequest):
    if not req.project_id:
        raise HTTPException(status_code=400, detail="project_id required")
    return _try_preview_logic(req.project_id)

@router.post("/preview_with_sources", response_model=PreviewResponse)
def preview_with_sources(req: PreviewRequest):
    if not req.project_id:
        raise HTTPException(status_code=400, detail="project_id required")
    # identisch, aber garantiert citations-Feld (auch wenn leer)
    out = _try_preview_logic(req.project_id)
    if out.citations is None:
        out.citations = []
    return out


@router.post("/preview_with_sources_stream")
def preview_with_sources_stream(req: PreviewRequest, accept: str | None = Header(default=None)):
    if not req.project_id:
        raise HTTPException(status_code=400, detail="project_id required")

    def gen():
        # Phase 1: Retrieval
        yield '{"diagnostics":{"stage":"retrieval"},"citations":[]}\n'
        # Phase 2: Compose
        yield '{"diagnostics":{"stage":"compose"}}\n'
        # Phase 3: Final (vollständiges Preview-Objekt)
        final = _try_preview_logic(req.project_id)
        import json
        yield json.dumps(final.model_dump()) + "\n"

    ct = "application/x-ndjson"
    return StreamingResponse(gen(), media_type=ct)
