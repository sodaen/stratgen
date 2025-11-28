# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import os, urllib.parse

router = APIRouter(tags=["export"])  # bewusst ohne Prefix (Kompatibilität)

def _safe_filename(name: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in ("-", "_", ".")) else "_" for ch in name)

def _resolve_file(p: Path) -> Path:
    if p.exists():
        return p
    p2 = Path(os.getcwd()) / p
    return p2 if p2.exists() else p

@router.get("/projects/{project_id}/export")
@router.post("/projects/{project_id}/export")
def export_project(
    project_id: str,
    format: str = Query("pptx", description="pptx|json"),
    filename: Optional[str] = Query(None, description="optional Download-Name"),
    dl: bool = Query(True, description="Bei JSON: dl=false → reine JSON-Antwort"),
    template_name: Optional[str] = Query(None),
    template_path: Optional[str] = Query(None),
):
    try:
        from backend import pptx_api as _pptx
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pptx_api import failed: {e}")

    # WICHTIG: reine Helper-Funktion (kein Body-Default mehr)
    try:
        res = _pptx.render_from_project(project_id, template_name=template_name, template_path=template_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"render failed: {e}")

    out_path = res.get("path") if isinstance(res, dict) else getattr(res, "path", None)
    if not out_path:
        raise HTTPException(status_code=500, detail="render did not return path")

    p = _resolve_file(Path(out_path))
    if not p.exists():
        raise HTTPException(status_code=500, detail=f"export file not found: {out_path}")

    if format.lower() == "json" and not dl:
        return {"ok": True, "path": str(p), "name": p.name}

    # Download als PPTX (sauberer Content-Disposition)
    download_name = filename or p.name
    ascii_name = _safe_filename(download_name)
    quoted = urllib.parse.quote(download_name)
    dispo = f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quoted}'

    resp = FileResponse(
        str(p),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=ascii_name,
    )
    resp.headers["Content-Disposition"] = dispo
    return resp

@router.get("/projects/{project_id}/export.md")
@router.post("/projects/{project_id}/export.md")
def export_project_markdown(project_id: str):
    # Projekt laden
    try:
        from backend import projects_api as _p  # type: ignore
        pj = _p.get_project(project_id)
    except Exception:
        pj = None
    if not pj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Markdown generieren (echter Service, sonst Fallback)
    md = None
    try:
        from services.markdown import project_to_markdown  # type: ignore
        md = project_to_markdown(pj)
    except Exception:
        title = (pj.get("outline") or {}).get("title") or pj.get("topic") or pj.get("customer_name") or f"Project {project_id}"
        md = f"# {title}\n\n_Markdown export fallback — formatter not available._\n"

    out_dir = Path("data/exports"); out_dir.mkdir(parents=True, exist_ok=True)
    slug_src = pj.get("slug") or pj.get("customer_name") or pj.get("customer") or "deck"
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in slug_src).strip("-") or "deck"
    fp = out_dir / f"deck-{slug}.md"
    fp.write_text(md, encoding="utf-8")
    return FileResponse(str(fp), media_type="text/markdown", filename=fp.name)

# Backwards-compat Alias
@router.get("/export/projects/{project_id}/export.md")
@router.post("/export/projects/{project_id}/export.md")
def export_project_markdown_alias(project_id: str):
    return export_project_markdown(project_id)

# Notion-Stub (GET/POST)
@router.get("/projects/{project_id}/export.notion")
@router.post("/projects/{project_id}/export.notion")
def export_project_notion(project_id: str):
    md = f"# Project {project_id}\n\n_Notion export stub (convert MD → Notion externally)._"
    return Response(content=md, media_type="text/markdown")
