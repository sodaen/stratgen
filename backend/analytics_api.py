# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.telemetry import log_event

router = APIRouter(prefix="/analytics", tags=["analytics"])  # öffentlich

class AnalyticsPayload(BaseModel):
    event: str = Field(..., description="Eventname, z.B. 'page_view'")
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

@router.post("/log")
def log_analytics(payload: AnalyticsPayload):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    # log_event erwartet EIN Dict (kein kwargs!)
    log_event({
        "event": data.get("event") or "unknown",
        "project_id": data.get("project_id"),
        "user_id": data.get("user_id"),
        "meta": data.get("meta") or {},
    })
    return {"ok": True}
