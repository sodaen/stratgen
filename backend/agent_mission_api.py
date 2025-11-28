from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend._mission_store import create, get

router = APIRouter(prefix="/agent/mission", tags=["agent"])

class Mission(BaseModel):
    objective: str
    audience: Optional[str] = None
    voice: Optional[str] = None
    constraints: Optional[str] = None

@router.post("/start")
def start(m: Mission):
    mid = create(m.dict())
    return {"ok": True, "mission_id": mid}

@router.get("/{mission_id}")
def read(mission_id: str):
    it = get(mission_id)
    if not it: raise HTTPException(404, "mission not found")
    return {"ok": True, "item": it}
