# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.telemetry import log_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackPayload(BaseModel):
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    rubric: Dict[str, Any] = Field(default_factory=dict)
    comment: Optional[str] = None

@router.post("/submit")
def submit(p: FeedbackPayload):
    log_feedback(p.model_dump())
    return {"ok": True}
