from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/outline", tags=["outline"])

# ---------- Modelle ----------
class OutlineInput(BaseModel):
    customer_name: str = Field(..., description="Kunde/Marke")
    topic: str = Field(..., description="Thema/Fragestellung")
    # Rohinputs (aus Briefs/Personas/Insights)
    brief_title: Optional[str] = None
    brief_bullets: List[str] = Field(default_factory=list)
    personas: List[Dict[str, Any]] = Field(default_factory=list)   # z.B. [{name, role, goals, pains, ...}]
    insights_bullets: List[str] = Field(default_factory=list)      # kurze Findings
    # Quellen (URL/Provider), duales Setup für spätere automatische Recherche
    urls: List[str] = Field(default_factory=list)
    providers: List[str] = Field(default_factory=list)  # z.B. ["statista","brandwatch","talkwalker"]
    # Optionen
    max_sections: int = 8
    max_bullets_per_section: int = 6

class OutlineSection(BaseModel):
    id: str
    title: str
    bullets: List[str] = []
    evidence: List[Dict[str, Any]] = []  # optional Verweise auf Quellen

class OutlineOut(BaseModel):
    ok: bool = True
    customer_name: str
    topic: str
    sections: List[OutlineSection]
    sources: List[Dict[str, Any]] = []

# ---------- Helpers ----------
def _mk_sources(urls: List[str], providers: List[str]) -> List[Dict[str, Any]]:
    srcs = [{"type":"url","value":u} for u in urls]
    srcs += [{"type":"provider","value":p} for p in providers]
    return srcs

def _truncate(xs: List[str], n: int) -> List[str]:
    return [str(x) for x in xs][:max(0, n)]

# ---------- Endpoint ----------
@router.post("/generate", response_model=OutlineOut, summary="Erzeugt eine Präsentations-Outline aus Brief/Personas/Insights")
def generate(req: OutlineInput = Body(...)):
    # Grundgerüst (klassische Deck-Struktur für Strategie/Konzept)
    skeleton = [
        ("sec_exec", "Executive Summary"),
        ("sec_context", "Ausgangslage & Zielbild"),
        ("sec_personas", "Zielgruppen/Personas"),
        ("sec_insights", "Schlüssel-Insights"),
        ("sec_strategy", "Strategische Leitlinien"),
        ("sec_actions", "Maßnahmen & Kanäle"),
        ("sec_kpi", "KPIs & Messkonzept"),
        ("sec_next", "Roadmap & Next Steps"),
    ][: max(1, req.max_sections)]

    sections: List[OutlineSection] = []

    # 1) Executive Summary – kurze Synthese
    if skeleton and skeleton[0][0] == "sec_exec":
        bullets = []
        if req.brief_title:
            bullets.append(f"Briefing: {req.brief_title}")
        if req.topic:
            bullets.append(f"Fokus-Thema: {req.topic}")
        if req.insights_bullets:
            bullets += _truncate([f"Insight: {b}" for b in req.insights_bullets], req.max_bullets_per_section - len(bullets))
        if not bullets:
            bullets = ["Kurzüberblick wird aus Daten generiert (Platzhalter)."]
        sections.append(OutlineSection(id="sec_exec", title="Executive Summary", bullets=bullets))

    # 2) Ausgangslage
    if any(i for i in skeleton if i[0] == "sec_context"):
        bullets = _truncate(
            (req.brief_bullets or []) + [f"Relevante Quellen: {', '.join(req.providers or [])}"],
            req.max_bullets_per_section
        )
        if not bullets:
            bullets = ["Ausgangslage/Marktumfeld (wird aus Quellen abgeleitet)."]
        sections.append(OutlineSection(id="sec_context", title="Ausgangslage & Zielbild", bullets=bullets))

    # 3) Personas
    if any(i for i in skeleton if i[0] == "sec_personas"):
        pb = []
        for p in req.personas[:3]:  # kompakt
            name = p.get("name") or p.get("role") or "Persona"
            goals = p.get("goals") or []
            pains = p.get("pains") or []
            pb.append(f"{name}: Ziele – {', '.join(goals[:2]) or 'n/a'}; Pain Points – {', '.join(pains[:2]) or 'n/a'}")
        if not pb:
            pb = ["Personas werden aus Daten generiert (Platzhalter)."]
        sections.append(OutlineSection(id="sec_personas", title="Zielgruppen/Personas", bullets=_truncate(pb, req.max_bullets_per_section)))

    # 4) Insights
    if any(i for i in skeleton if i[0] == "sec_insights"):
        ib = _truncate(req.insights_bullets, req.max_bullets_per_section)
        if not ib:
            ib = ["Noch keine Insights übergeben – bitte research/insights befüllen oder URLs/Provider angeben."]
        sections.append(OutlineSection(id="sec_insights", title="Schlüssel-Insights", bullets=ib))

    # 5) Strategie-Leitlinien (heuristisch aus Inputs)
    if any(i for i in skeleton if i[0] == "sec_strategy"):
        hints = []
        if any("ROI" in b.upper() for b in (req.insights_bullets or [])):
            hints.append("Content-Strategie mit ROI-Belegen (Cases, Benchmarks).")
        if any("PEER" in b.upper() for b in (req.insights_bullets or [])):
            hints.append("Social Proof & Peer-Reviews als zentrales Asset.")
        if not hints:
            hints = ["Leitlinien werden aus Datensynthese abgeleitet (Platzhalter)."]
        sections.append(OutlineSection(id="sec_strategy", title="Strategische Leitlinien", bullets=_truncate(hints, req.max_bullets_per_section)))

    # 6) Maßnahmen & Kanäle (Stub)
    if any(i for i in skeleton if i[0] == "sec_actions"):
        actions = [
            "Always-on LinkedIn (C-Level & IT-Entscheider) mit Proof-Assets",
            "Webinare/Tech-Talks mit Q&A (Lead-Qualifizierung)",
            "Landingpages je Persona (Kaufkriterien adressieren)",
        ]
        sections.append(OutlineSection(id="sec_actions", title="Maßnahmen & Kanäle", bullets=_truncate(actions, req.max_bullets_per_section)))

    # 7) KPI (Stub)
    if any(i for i in skeleton if i[0] == "sec_kpi"):
        kpis = [
            "SQL/OPP-Rate aus MQLs",
            "Pipeline-Beitrag nach Kanal",
            "Demo/POC-Conversion",
        ]
        sections.append(OutlineSection(id="sec_kpi", title="KPIs & Messkonzept", bullets=_truncate(kpis, req.max_bullets_per_section)))

    # 8) Roadmap (Stub)
    if any(i for i in skeleton if i[0] == "sec_next"):
        nx = ["Pilot Q1 (2 Personas, 1 Use Case)", "Skalierung Q2–Q3", "Review & Iteration vierteljährlich"]
        sections.append(OutlineSection(id="sec_next", title="Roadmap & Next Steps", bullets=_truncate(nx, req.max_bullets_per_section)))

    return OutlineOut(
        ok=True,
        customer_name=req.customer_name,
        topic=req.topic,
        sections=sections,
        sources=_mk_sources(req.urls, req.providers),
    )
