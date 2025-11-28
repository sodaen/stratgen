# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/messaging", tags=["messaging"])

class MatrixReq(BaseModel):
    personas: List[Dict[str, Any]] = []
    value_props: List[str] = ["Schneller", "Günstiger", "Sicherer"]

@router.post("/matrix")
def messaging_matrix(body: dict = Body(...)):
    personas = body.get("personas") or [{"name": "Generic"}]
    # Akzeptiere sowohl value_props (snake_case) als auch valueProps (camelCase)
    value_props = body.get("value_props") or body.get("valueProps") or ["Schneller", "Günstiger", "Sicherer"]
    rows = []
    for p in personas:
        name = p.get("name", "Persona")
        rows.append({
            "persona": name,
            "messages": [f"{vp} für {name}" for vp in value_props]
        })
    return {"ok": True, "matrix": rows}
