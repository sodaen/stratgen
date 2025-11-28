# -*- coding: utf-8 -*-

from __future__ import annotations

from fastapi import APIRouter
import time, os

try:
    from services.compat import resolve_style
except Exception:
    resolve_style = None  # Fallback

router = APIRouter()

@router.get("/health", tags=["health"])
def health():
    styles = {}
    for k in ("brand", "minimal"):
        ok = False
        try:
            if resolve_style:
                s = resolve_style(k)
                ok = isinstance(s, dict) and bool(s)
        except Exception:
            ok = False
        styles[k] = ok

    return {
        "status": "ok",
        "ts": int(time.time()),
        "env": {"APP_ENV": os.getenv("APP_ENV", "dev")},
        "styles": styles,
    }
