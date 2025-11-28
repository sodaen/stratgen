# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML_FILE = Path(__file__).resolve().parent / "ui_static.html"

@router.get("/ui", response_class=HTMLResponse)
def get_ui() -> HTMLResponse:
    html = HTML_FILE.read_text(encoding="utf-8")
    return HTMLResponse(html)

@router.head("/ui")
def head_ui() -> Response:
    # Einfach 200 – keine Body/Headers nötig
    return Response(status_code=200)
