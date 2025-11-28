# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path
import unicodedata, urllib.parse

router = APIRouter(tags=["exports"])
EXPORTS_DIR = Path("data/exports").resolve()

def _safe_path(name: str) -> Path:
    base = Path(name).name  # no path traversal
    fp = (EXPORTS_DIR / base)
    try:
        rp = fp.resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Not Found")
    if EXPORTS_DIR not in rp.parents and rp != EXPORTS_DIR:
        raise HTTPException(status_code=400, detail="Bad name")
    return rp

def _guess_mime(path: Path) -> str:
    if path.suffix.lower() == ".pptx":
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return "application/octet-stream"

def _content_disposition(basename: str) -> str:
    ascii_fb = unicodedata.normalize("NFKD", basename).encode("ascii","ignore").decode("ascii") or "export.pptx"
    ascii_fb = ascii_fb.replace(";", " ").replace("\\", " ").replace('"', " ")
    quoted = urllib.parse.quote(basename, safe="")
    return f'attachment; filename="{ascii_fb}"; filename*=UTF-8\'\'{quoted}'

@router.head("/exports/download/{name}")
def head_download(name: str):
    fp = _safe_path(name)
    st = fp.stat()
    headers = {
        "Content-Type": _guess_mime(fp),
        "Content-Length": str(st.st_size),
        "Content-Disposition": _content_disposition(fp.name),
    }
    # Nur Header, kein Body
    return Response(status_code=200, headers=headers)

@router.get("/exports/download/{name}")
def get_download(name: str):
    fp = _safe_path(name)
    resp = FileResponse(path=str(fp), media_type=_guess_mime(fp))
    resp.headers["Content-Disposition"] = _content_disposition(fp.name)
    return resp
