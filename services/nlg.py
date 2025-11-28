
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List

def _cap(s:str)->str: return (s or "").strip().capitalize()

def mod_exec_summary(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    cust = project.get("customer_name") or "Client"
    topic = project.get("topic") or "Initiative"
    bullets = [
        f"Ziel: {_cap(topic)} erfolgreich im Markt verankern.",
        "Fokus-Segmente priorisiert (Size × Fit × Reach).",
        "Kernbotschaften + RTBs entlang Customer Journey.",
        "Kanal-Mix mit klaren Verantwortlichkeiten, Budget-Guardrails.",
        "KPIs & Messplan mit monatlichem Review."
    ]
    return {"title":"Executive Summary","bullets":bullets,"notes":f"{cust} – Überblick & Empfehlungen"}

def mod_audience(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    segs = []
    # sehr einfache Heuristik aus Outline
    for s in (project.get("outline") or {}).get("sections", []):
        if (s.get("title") or "").lower().startswith("ziel"):
            segs += s.get("bullets") or []
    segs = segs or ["Primärsegment", "Sekundärsegment"]
    bullets = [f"Segment: {_cap(x)} – Needs/Jobs to be done, Pain/Gain" for x in segs[:5]]
    return {"title":"Zielgruppen & Bedürfnisse","bullets":bullets, "notes":"Basis für Positionierung & Kanäle"}

def mod_insights(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    hints = []
    if facts.get("tables"):
        hints.append("Tabellarische Markt-/Konkurrenzdaten analysiert.")
    if facts.get("text_blobs"):
        hints.append("Qualitative Signale aus Textquellen verdichtet.")
    hints = hints or ["Primäre Recherche erforderlich."]
    bullets = ["Wichtigste Treiber & Barrieren pro Segment", "Kaufkriterien & Entscheiderlogik", *hints]
    return {"title":"Insights & Marktlogik","bullets":bullets, "notes":"Ableitung von RTBs & Content-Themen"}

def mod_positioning(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    cust = project.get("customer_name") or "Marke"
    bullets = [
        f"Value Proposition: {cust} löst X besser als Wettbewerb",
        "RTBs: Proofs/Belege (Cases, Zertifizierungen, Zahlen)",
        "Differenzierung: 1–2 klare Kanten, kein Feature-Overload"
    ]
    return {"title":"Positionierung & RTBs","bullets":bullets, "notes":"Klar, glaubwürdig, verteidigbar"}

def mod_messaging(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Master-Message (oberhalb der Funnel-Phase konsistent)",
        "Per Segment: Key Message + 2–3 Sub-Claims",
        "Tonality: präzise, nutzenorientiert; Social-Proof prominent"
    ]
    return {"title":"Messaging Framework","bullets":bullets, "notes":"Mapping auf Assets & Kanäle"}

def mod_channels(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "TOFU: Reach/Attention (Paid Social/Video, PR-Aufschlag)",
        "MOFU: Education/Nurture (Web, SEO, Email, Webinar)",
        "BOFU: Conversion (SEA, Retargeting, Sales-Enablement)",
        "Owned-First: Website als Content-Hub",
    ]
    return {"title":"Kanalstrategie (Funnel)","bullets":bullets, "notes":"Verknüpfung mit Journey & Creatives"}

def mod_kpis(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "TOFU: Impressions, Reach, VTR",
        "MOFU: CTR, Time on Site, Leads, MQLs",
        "BOFU: SQLs, Win-Rate, CAC, Payback",
        "Attribution & MMM (später) vorbereiten"
    ]
    return {"title":"KPIs & Messplan","bullets":bullets, "notes":"Dashboards & Review-Rhythmus festlegen"}

def mod_roadmap(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Phase 0: Research & Setup (2–4 Wochen)",
        "Phase 1: Launch (Assets, Channels, Tracking)",
        "Phase 2: Optimize (A/B, Creative, Bidding)",
        "Phase 3: Scale (Budget, neue Kanäle/Segmente)"
    ]
    return {"title":"Roadmap & Meilensteine","bullets":bullets, "notes":"Abhängigkeiten & Ressourcen"}

MODULES = {
    "exec": mod_exec_summary,
    "audience": mod_audience,
    "insights": mod_insights,
    "positioning": mod_positioning,
    "messaging": mod_messaging,
    "channels": mod_channels,
    "kpis": mod_kpis,
    "roadmap": mod_roadmap,
}

MODULES["kpis"] = mod_kpis
