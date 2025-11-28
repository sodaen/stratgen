from fastapi import APIRouter, Query
from typing import List
import pathlib, json

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.get("/events", summary="Tail telemetry events (last N)", operation_id="telemetry_tail__telemetry_events")
def events(limit: int = Query(50, ge=1, le=1000)) -> List[dict]:
    p = pathlib.Path("data/telemetry/events.jsonl")
    if not p.exists(): 
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out
