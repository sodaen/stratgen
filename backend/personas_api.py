# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/personas", tags=["personas"])

class PersonasReq(BaseModel):
    product: str = "B2B SaaS"
    countries: List[str] = ["DE"]

@router.post("/suggest")
def personas_suggest(req: PersonasReq = Body(...)):
    personas = [
        {"name": "Digital Lead", "goals": ["Effizienz"], "pains": ["Legacy"], "objections": ["Budget"]},
        {"name": "CMO", "goals": ["Growth"], "pains": ["Attribution"], "objections": ["Brand Risk"]},
    ]
    return {"ok": True, "personas": personas}
