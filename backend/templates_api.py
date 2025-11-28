# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from services.templates import save_template, list_templates, inspect_template
from fastapi import Header

router = APIRouter(prefix="/templates", tags=["templates"])

# geschützter Upload
def require_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    # gleiche Logik wie im Haupt-API
    import os
    if (os.getenv("API_KEY","dev")) != (x_api_key or ""):
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/upload", dependencies=[Depends(require_api_key)])
async def upload_template(name: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=422, detail="Only .pptx allowed")
    # Temporär speichern
    import tempfile, shutil
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp.flush()
        res = save_template(tmp.name, name)
    return res

@router.get("/list")
def list_t():
    return {"items": list_templates()}

@router.get("/inspect/{name}")
def insp(name: str):
    return inspect_template(name)
