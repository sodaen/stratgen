# -*- coding: utf-8 -*-
from fastapi import APIRouter
try:
    from backend.projects_fix_api import router as _r
except Exception:
    _r = APIRouter()

router = APIRouter()
router.include_router(_r)

# einige Varianten erwarten diesen Namen:
router_public = router

# Sentinel für Guards/Introspection
@router.get("/projects/_present")
def _present_projects_api():
    return {"ok": True, "module": __name__}
