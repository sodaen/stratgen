from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend._agent_state import list_runs, get_run

router = APIRouter(prefix="/agent/state", tags=["agent"])

@router.get("/runs")
def list_recent(limit: int = Query(50, ge=1, le=500), status: Optional[str] = None):
    return {"ok": True, "items": list_runs(limit, status)}

@router.get("/{run_id}")
def read_one(run_id: str):
    it = get_run(run_id)
    if not it:
        raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True, "item": it}
