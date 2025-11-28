# -*- coding: utf-8 -*-

from __future__ import annotations

import os, time, subprocess
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["debug"])

def _git_rev() -> str:
    try:
        return subprocess.check_output(["git","rev-parse","--short","HEAD"], text=True).strip()
    except Exception:
        return "unknown"

@router.get("/debug/info")
def debug_info():
    return JSONResponse({
        "ok": True,
        "ts": time.time(),
        "env": os.getenv("APP_ENV","dev"),
        "cors_origins": os.getenv("CORS_ORIGINS","*"),
        "rate_limit": {
            "rps": float(os.getenv("RATE_LIMIT_RPS","6")),
            "burst": float(os.getenv("RATE_LIMIT_BURST","12")),
        },
        "git": _git_rev(),
    })
