# -*- coding: utf-8 -*-
from fastapi import APIRouter
router = APIRouter(prefix="/dev", tags=["dev"])
@router.get("/smoke")
def smoke():
    import time
    return {"ok": True, "ts": time.time()}
