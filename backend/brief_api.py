from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/briefs", tags=["briefs"])

class BriefReq(BaseModel):
    customer_name: str = Field(..., description="Kunde/Marke")
    topic: str = Field(..., description="Thema/Fragestellung für das Briefing")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Signals aus Files/DS (z.B. insights/personas)")
    urls: List[str] = Field(default_factory=list, description="Optionale Web-Quellen")
    providers: List[str] = Field(default_factory=list, description="Externe Provider-Keys (z.B. 'statista','brandwatch')")
    max_bullets: int = 8

class BriefOut(BaseModel):
    ok: bool = True
    title: str
    bullets: List[str]
    sources: List[Dict[str, Any]] = []

@router.post("/generate", response_model=BriefOut)
def generate(req: BriefReq = Body(...)):
    """
    Stub: aggregiert vorhandene Insights/Personas + (später) Web/APIs.
    Aktuell: nutzt nur vorhandene Inputs, URLs/Providers werden geloggt.
    """
    # 1) Vorhandene interne Signale nutzen
    bullets = []
    ins = req.inputs or {}
    for b in (ins.get("insights_bullets") or [])[: req.max_bullets]:
        bullets.append(str(b))

    if not bullets:
        bullets = [f"Kein Seed vorhanden – Briefing zu '{req.topic}' wird vorbereitet."]

    # 2) Quellenobjekte vorbereiten (Stub)
    srcs = []
    for u in req.urls:
        srcs.append({"type": "url", "value": u})
    for p in req.providers:
        srcs.append({"type": "provider", "value": p})

    return BriefOut(
        ok=True,
        title=f"Research-Brief: {req.topic}",
        bullets=bullets,
        sources=srcs,
    )
