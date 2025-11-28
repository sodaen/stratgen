from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import json, time

router = APIRouter(prefix="/strategy", tags=["strategy"])

STRAT_DIR = Path("data/strategies")
STRAT_DIR.mkdir(parents=True, exist_ok=True)


class StrategyIn(BaseModel):
    mission_id: Optional[int] = None
    mission_ref: Optional[str] = None
    briefing: str
    size: str = "medium"
    audience: str = "Management"
    tone: Optional[str] = None
    lang: str = "de"
    title: Optional[str] = None
    # RAG-Kontext (vom Agent vorbereitet)
    context: Optional[List[str]] = None


def _default_slides(size: str = "medium") -> List[dict]:
    n = {"small": 6, "medium": 12, "large": 20}.get(size, 12)
    return [
        {
            "title": f"Slide {i}",
            "bullets": [
                "Inhalt aus LLM oder Fallback",
                "Detail / Maßnahme",
                "Nächster Schritt",
            ],
        }
        for i in range(1, n + 1)
    ]


@router.post("/gen")
def strategy_gen(body: StrategyIn):
    # Hier: Fallback-LLM-Text – reicht für Sanity-Tests
    llm_raw = (
        ' Titel der Präsentation: "Strategie basierend auf Briefing"\n\n'
        "Strategische Ziele:\n1. ...\n\nKernbotschaften:\n1. ...\n"
    )

    data = {
        "name": f"strategy-{int(time.time())}.json",
        "mission_id": body.mission_id,
        "mission_ref": body.mission_ref,
        "briefing": body.briefing,
        "size": body.size,
        "audience": body.audience,
        "tone": body.tone,
        "lang": body.lang,
        "created_at": time.time(),
        "updated_at": time.time(),
        "llm_raw": llm_raw,
        "title": body.title or "Strategie basierend auf Briefing",
        "goals": [
            "Klarheit über Zielgruppe schaffen",
            "Content- und Kanalstrategie definieren",
            "KI-Anteile planbar machen",
        ],
        "core_messages": [
            "KI ist ein Enabler, kein Selbstzweck",
            "Content muss kanal- und zielgruppenspezifisch sein",
            "Lernen aus produzierten Assets ist Pflicht",
        ],
        "slides": _default_slides(body.size),
        "status": "generated",
        "used_contents": [],
        "context_used": body.context or [],
        "context_sources": [],
    }

    (STRAT_DIR / data["name"]).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"ok": True, "data": data}


class StrategyReviseIn(BaseModel):
    name: str
    use_critic: bool = False
    critic_name: Optional[str] = None
    add_agenda: bool = True
    add_cta: bool = True


@router.post("/revise")
def strategy_revise(body: StrategyReviseIn):
    p = STRAT_DIR / body.name
    if not p.exists():
        raise HTTPException(status_code=404, detail="strategy not found")
    data = json.loads(p.read_text(encoding="utf-8"))

    added = []
    if body.add_agenda:
        data["slides"].insert(
            0,
            {
                "title": "Agenda",
                "bullets": ["Ausgangslage", "Ziele", "Roadmap"],
            },
        )
        added.append("agenda")

    if body.add_cta:
        data["slides"].append(
            {
                "title": "Nächste Schritte",
                "bullets": ["Owner & Timing", "KPIs", "Risiken"],
            }
        )
        added.append("cta")

    data["updated_at"] = time.time()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "data": data, "added": added}


@router.get("/{name}")
def strategy_get(name: str):
    p = STRAT_DIR / name
    if not p.exists():
        raise HTTPException(status_code=404, detail="strategy not found")
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"ok": True, "data": data}
