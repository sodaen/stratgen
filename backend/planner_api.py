from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
import http.client
import json

router = APIRouter(prefix="/planner", tags=["planner"])

class PlanRequest(BaseModel):
    customer_name: str
    topic: str
    goals: List[str] = Field(default_factory=list)
    persona: Optional[str] = None
    k: int = 3  # wie viele Knowledge-Treffer einbeziehen

class PlanResponse(BaseModel):
    customer_name: str
    topic: str
    knowledge_hits: List[str]
    outline: List[dict]

def _knowledge_search_localhost(query: str, k: int = 3) -> List[str]:
    # sehr robust & ohne zusätzliche Abhängigkeiten (http.client)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", 8011, timeout=2)
        path = f"/knowledge/search?q={query}&k={k}"
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status != 200:
            return []
        data = json.loads(resp.read().decode("utf-8"))
        hits = data.get("results", [])
        # wir nehmen den (Datei-)Pfad als simple Referenz
        return [h.get("path") or h.get("id") or "" for h in hits if h]
    except Exception:
        return []

@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest) -> PlanResponse:
    # 1) Knowledge-Suche: Kunde/Topic als Query
    query = f"{req.customer_name} {req.topic}"
    hits = _knowledge_search_localhost(query, k=max(1, req.k))

    # 2) Heuristische Outline (später mit LLM anreicherbar)
    outline = [
        {"kind": "title", "layout_hint": "Title Slide",
         "title": f"{req.topic} – {req.customer_name}"},
        {"kind": "agenda", "layout_hint": "Title and Content",
         "title": "Agenda", "bullets": [
            "Ziele & Kontext", "Zielgruppen & Insights",
            "Strategie & Taktiken", "KPIs & Roadmap"
         ]},
        {"kind": "goals", "layout_hint": "Title and Content",
         "title": "Ziele", "bullets": (req.goals or ["Klares Zielbild definieren"])},
        {"kind": "insights", "layout_hint": "Title and Content",
         "title": "Insights (aus Knowledge)",
         "bullets": hits[:5] if hits else ["(keine lokalen Treffer – bitte Knowledge ausbauen)"]},
        {"kind": "strategy", "layout_hint": "Title and Content",
         "title": "Strategischer Ansatz",
         "bullets": [
            "Positionierung & Value Proposition",
            "Kanalpriorisierung",
            "Kreativleitplanken"
         ]},
        {"kind": "kpis", "layout_hint": "Title and Content",
         "title": "KPIs & Messplan",
         "bullets": ["Umsatz", "CAC", "CTR", "ROAS"]},
        {"kind": "roadmap", "layout_hint": "Title and Content",
         "title": "Roadmap & Nächste Schritte",
         "bullets": ["Quick Wins (0-30 Tage)", "Pilot (30-90 Tage)", "Scale (90+ Tage)"]}
    ]

    return PlanResponse(
        customer_name=req.customer_name,
        topic=req.topic,
        knowledge_hits=hits,
        outline=outline,
    )
