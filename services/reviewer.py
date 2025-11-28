# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List

def _titles(slides: List[Dict[str, Any]]) -> List[str]:
    return [ (s.get("title") or "").strip() for s in (slides or []) ]

def review_slide_plan(slides: List[Dict[str, Any]], outline: Dict[str, Any] | None = None, facts: Dict[str, Any] | None = None, **kwargs) -> Dict[str, Any]:
    issues: List[str] = []
    suggs:  List[str] = []

    if not slides:
        return {"score": 0, "issues": ["Kein Slide-Plan."], "suggestions": ["Mind. 6 Slides mit sinnvollen Titeln erstellen."]}

    # 1) Mindestlänge
    if len(slides) < 6:
        issues.append(f"Deck ist sehr kurz ({len(slides)} < 6).")
        suggs.append("Mindestens 6–10 Slides einplanen (Titel, Agenda, 3–6 Sektionen, KPIs/Quellen).")

    # 2) Doppelte Titel
    ts = _titles(slides)
    dups = sorted({t for t in ts if t and ts.count(t) > 1})
    if dups:
        issues.append("Doppelte Folientitel gefunden.")
        suggs.append("Titel differenzieren (z. B. 'Ziele (Marketing)' vs. 'Ziele (Produkt)').")

    # 3) Leere Section-Slides
    empty_sections = [s for s in slides if (s.get("kind")=="section" and not (s.get("bullets") or s.get("notes")))]
    if empty_sections:
        issues.append(f"{len(empty_sections)} Section-Slide(s) ohne Inhalt.")
        suggs.append("Mindestens 1–3 prägnante Bullets je Section ergänzen.")

    # 4) Agenda-Slide bei >=3 Sections
    num_sections = sum(1 for s in slides if s.get("kind")=="section")
    has_agenda = any(s.get("kind")=="agenda" for s in slides)
    if num_sections >= 3 and not has_agenda:
        issues.append("Keine Agenda-Slide.")
        suggs.append("Nach Titel eine Agenda einfügen (alle Section-Titel als Bullets).")

    # 5) KPIs wenn metrics vorhanden
    has_kpis = any(s.get("kind")=="kpis" for s in slides)
    # weiche Heuristik: wenn eine Section 'KPIs' heißt, ist es faktisch ok
    if not has_kpis and any((s.get("title") or "").lower().startswith("kpi") for s in slides):
        has_kpis = True

    # 6) Verbotene Platzhalter
    bad = [s for s in slides if "tbd" in (s.get("notes") or "").lower()]
    if bad:
        issues.append("Platzhalter 'TBD' gefunden.")
        suggs.append("'TBD' durch konkrete Hinweise ersetzen.")

    # Score Heuristik
    score = 10
    penalties = 0
    for _ in issues:
        penalties += 1
    score = max(1, score - penalties)

    return {"score": score, "issues": issues, "suggestions": suggs}
