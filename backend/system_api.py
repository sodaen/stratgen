from __future__ import annotations

# System-Endpunkte: Health & Version (ohne Auth)

import os
import subprocess
from fastapi import APIRouter

router = APIRouter(tags=["system"])

def _git_rev() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

@router.get("/_health")
def health():
    return {"ok": True, "service": "stratgen", "pid": os.getpid()}

@router.get("/_version")
def version():
    return {"ok": True, "version": _git_rev()}
