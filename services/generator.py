# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Optional
from copy import deepcopy
import time, re

# ------------------------------------------------------------
# Kanonische Module & Layout-Hints
# ------------------------------------------------------------
CANONICAL_MODULES = [
    "Executive Summary",
    "ROI & Business Case",
    "Risiken & Migrationspfad",
    "Roadmap & Pilot",
    "Use Cases",
    "Integration & Workflow",
    "Compliance & DSGVO",
    "Change Management",
    "Training & Enablement",
    "Next Steps",
]

MODULE_HINTS = {
    "Executive Summary": "Content",
    "ROI & Business Case": "Content",
    "Risiken & Migrationspfad": "Content",
    "Roadmap & Pilot": "Content",
    "Use Cases": "Content",
    "Integration & Workflow": "Content",
    "Compliance & DSGVO": "Content",
    "Change Management": "Content",
    "Training & Enablement": "Content",
    "Next Steps": "Content",
}

def _norm_title(t: str) -> str:
    return re.sub(r'\s+',' ', (t or '').strip()).lower()

def _ensure_canonical_modules(proj: dict, plan: list) -> list:
    """Hält die Titelfolie vorn, erzwingt alle CANONICAL_MODULES in definierter Reihenfolge
    (mit Platzhaltern), hängt übrige Slides danach an. Idempotent."""
    if not isinstance(plan, list):
        plan = []

    # 1) Titelfolie vorne sichern
    title_idx = None
    for i, s in enumerate(plan):
        if (s or {}).get("layout_hint") == "Title" or (s or {}).get("kind") == "title":
            title_idx = i
            break
    title_slide = plan[title_idx] if title_idx is not None else None

    # 2) map vorhandener Titel (normalisiert) -> Slide (erste Vorkommnis)
    first_by_title = {}
    for s in plan:
        nt = _norm_title((s or {}).get("title"))
        if nt and nt not in first_by_title:
            first_by_title[nt] = s

    # 3) Kanon in definierter Reihenfolge aufbauen
    ordered = []
    for ct in CANONICAL_MODULES:
        nt = _norm_title(ct)
        if nt in first_by_title:
            ordered.append(first_by_title[nt])
        else:
            hint = MODULE_HINTS.get(ct, "Content")
            ordered.append({"layout_hint": hint, "title": ct, "bullets": [], "notes": "Platzhalter"})

    # 4) übrige (nicht-kanonische) Slides anhängen (ohne Duplikate)
    canon_norms = set(_norm_title(s.get("title")) for s in ordered)
    rest = []
    for i, s in enumerate(plan):
        if i == title_idx:
            continue
        nt = _norm_title((s or {}).get("title"))
        if nt and nt in canon_norms:
            continue
        rest.append(s)

    new_plan = []
    if title_slide:
        new_plan.append(title_slide)
    new_plan.extend(ordered)
    new_plan.extend(rest)

    # Notes-Fallbacks
    for s in new_plan:
        if not (s.get("notes") or "").strip():
            s["notes"] = "Hinweise für Presenter."
        s.setdefault("bullets", [])
        s.setdefault("layout_hint", "Content")
    return new_plan

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _now() -> int:
    return int(time.time())

def _as_int(v, default: Optional[int]) -> int:
    try:
        return int(v)
    except Exception:
        return default if default is not None else 0

def _norm(s: Optional[str]) -> str:
    return (s or "").strip()

def _norm_text(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '').strip())

# ------------------------------------------------------------
# Slides (Bausteine)
# ------------------------------------------------------------
def _title_slide(customer: str, topic: str) -> Dict[str, Any]:
    return {"layout_hint": "Title", "title": topic or "Strategie-Deck", "bullets": [customer] if customer else [], "notes": ""}

def _exec_summary(brief: str) -> Dict[str, Any]:
    return {
        "layout_hint": "Title and Content",
        "title": "Executive Summary",
        "bullets": [
            "Ziel: Zeitersparnis & Qualitätskonsistenz in der Postproduktion",
            "Ansatz: KI-Assist (Transkription, Rough Cut, Subtitles, QC)",
            "Integration: Nahtlos in bestehende Workflows/NLE",
            "Erfolgskriterien: schneller ROI, kontrolliertes Risiko",
        ],
        "notes": brief or "",
    }

def _roi_business_case() -> Dict[str, Any]:
    return {
        "layout_hint": "Title and Content",
        "title": "ROI & Business Case",
        "bullets": [
            "Baseline: manueller Aufwand (Transkript, Untertitel, QC)",
            "Uplift: 30–60% Zeiteinsparung bei wiederkehrenden Tasks",
            "Kostenblöcke: Lizenzen, Inferenz, Integration/Enablement",
            "Payback: 6–12 Monate (Pilot → stufenweiser Rollout)",
        ],
        "notes": "Später mit Realwerten (Stunden, Raten, Volumen) befüllen.",
    }

def _risiken_migrationspfad() -> Dict[str, Any]:
    return {
        "layout_hint": "Title and Content",
        "title": "Risiken & Migrationspfad",
        "bullets": [
            "Qualität/Konsistenz: Messpunkte & manuelle Gates",
            "Datenschutz/IP: On-Prem/Private Inference wo nötig",
            "Change Mgmt: Schulungen, Playbooks, Triage-Prozess",
            "Fallbacks: Manuelle Pfade bleiben nutzbar",
        ],
        "notes": "Risiken mit DRI und Mitigationsmatrix versehen.",
    }

def _roadmap_pilot() -> Dict[str, Any]:
    return {
        "layout_hint": "Title and Content",
        "title": "Roadmap & Pilot",
        "bullets": [
            "Phase 0 (2–3 W): Use-Case-Fit & KPI-Definition",
            "Phase 1 (2–4 W): Pilot – 1–2 Sendestrecken",
            "Phase 2 (6–8 W): Rollout – schrittweise Erweiterung",
            "Phase 3: Optimierung – Feintuning & Automationsgrade",
        ],
        "notes": "Pro Phase: Owner, KPIs, Abnahmekriterien klar definieren.",
    }

def _use_cases_overview(uclist: List[str]) -> Dict[str, Any]:
    bullets = [f"• {uc}" for uc in uclist] if uclist else ["Auto-Transkription", "Smart Rough Cut", "Auto-Subtitles", "QC-Assist"]
    return {"layout_hint": "Title and Content", "title": "Use Cases", "bullets": bullets, "notes": "Pro UC später: Inputs → Steps → Outputs → Messgrößen → Risiken."}

_UC_PATTERNS = [
    (r"transkrip", "Auto-Transkription"),
    (r"rough\s*cut|szenen|schnitt", "Smart Rough Cut"),
    (r"subtitle|untertitel", "Auto-Subtitles"),
    (r"\bqc\b|quality|qualitäts", "QC-Assist"),
]

def _extract_use_cases(brief: str) -> List[str]:
    b = (brief or "").lower()
    found = []
    for pat, label in _UC_PATTERNS:
        if re.search(pat, b):
            found.append(label)
    if not found:
        found = ["Auto-Transkription", "Smart Rough Cut", "Auto-Subtitles", "QC-Assist"]
    return found

def _uc_detail_slide(uc: str) -> Dict[str, Any]:
    bullets = {
        "Auto-Transkription": [
            "Mehrsprachig, Sprechertrennung (wo möglich)",
            "Timecodes/Marker für NLE, Export als Text/EDL/JSON",
            "Qualitätssicherung: WER/Konfidenz",
        ],
        "Smart Rough Cut": [
            "Szenenerkennung, Stille/Fehlerschnitt, Marker",
            "Automatische Vorschläge – Editor behält Kontrolle",
            "Versionssichere Übergabe in NLE",
        ],
        "Auto-Subtitles": [
            "Mehrsprachig, Styleguides, Timing/Kerning",
            "Export: SRT/WEBVTT/EBU-STL, Burn-In optional",
            "Qualität: Lesbarkeit, LPS, max. CPS",
        ],
        "QC-Assist": [
            "Checks: Loudness, Blacks, Artefakte, Color Hints",
            "Reports mit Hinweisen, Confidence, Jump-to-Frame",
            "Manuelle Freigabe bleibt Gate",
        ],
    }.get(uc, ["Beschreibung & Schritte", "Inputs/Outputs", "Risiken/Owner"])
    return {"layout_hint": "Title and Content", "title": f"Use Case – {uc}", "bullets": bullets, "notes": ""}

def _uc_kpi_slide(uc: str) -> Dict[str, Any]:
    return {
        "layout_hint": "Title and Content",
        "title": f"KPI & Impact – {uc}",
        "bullets": [
            "Zeit: Vor/Nach (Std/Asset) · Ziel: −30…−60%",
            "Qualität: Fehlerrate ↓ · Konsistenz ↑ (Messpunkte)",
            "Kosten: Lizenz/Inferenz/Enablement vs. Einsparungen",
            "Risiko/Owner: DRI, Fallback, QA-Gates, Rollback",
        ],
        "notes": "Später mit konkreten Basiswerten & Payback-Kalkulation füllen.",
    }

def _from_outline(outline: Dict[str, Any], brief: str) -> List[Dict[str, Any]]:
    slides: List[Dict[str, Any]] = []
    titles = [(s.get("title") or "").strip() for s in (outline or {}).get("sections", [])]
    ucs = _extract_use_cases(brief)

    for t in titles:
        key = t.lower()
        if "executive" in key:
            slides.append(_exec_summary(brief))
        elif "roi" in key or "business" in key:
            slides.append(_roi_business_case())
        elif "risiken" in key or "migration" in key:
            slides.append(_risiken_migrationspfad())
        elif "roadmap" in key or "pilot" in key:
            slides.append(_roadmap_pilot())
        elif "use case" in key or "use-case" in key or "usecases" in key or "use cases" in key:
            slides.append(_use_cases_overview(ucs))
            for uc in ucs:
                slides.append(_uc_detail_slide(uc))
                slides.append(_uc_kpi_slide(uc))
        else:
            slides.append({"layout_hint": "Section Header", "title": t or "Sektion", "bullets": [], "notes": ""})
    return slides

def _ensure_compliance_slide(plan: List[Dict[str, Any]]) -> None:
    try:
        has = any(("compliance" in str(s.get("title","")).lower()) or ("dsgvo" in str(s.get("title","")).lower()) for s in (plan or []))
        if not has:
            plan.append({
                "layout_hint": "Content",
                "title": "Compliance & DSGVO",
                "bullets": ["Datenschutz & Betriebsrat", "Provider-/Modellauswahl & Logs", "Retention, Löschung, Audit"],
                "notes": "DSGVO, AVV, Datenflüsse, Protokollierung."
            })
    except Exception:
        pass

def _split_use_cases(brief: str) -> list[str]:
    if not brief:
        return []
    parts = re.split(r'[\n;,]+', brief)
    out = []
    for x in parts:
        xx = _norm_text(x)
        if not xx:
            continue
        xx = re.sub(r'(?i)^\s*use\s*cases?\s*:\s*', '', xx)
        xx = re.sub(r'\.\s*$', '', xx)
        if len(xx) >= 3 and not re.match(r'(?i)unternehmensbriefing', xx):
            out.append(xx)
    seen = set(); uniq=[]
    for x in out:
        k = x.lower()
        if k not in seen:
            uniq.append(x); seen.add(k)
    return uniq[:8]

def _enrich_pro_plan(proj: dict, plan: list) -> list:
    titles_l = [(s.get("title") or "").strip().lower() for s in plan]
    if not any("compliance" in t or "dsgvo" in t for t in titles_l):
        try:
            idx = titles_l.index("change management")
        except ValueError:
            idx = len(plan)
        plan.insert(idx, {
            "layout_hint": "Content",
            "title": "Compliance & DSGVO",
            "bullets": ["Datenschutz & Betriebsrat", "Provider-/Modellauswahl & Logs", "Retention, Löschung, Audit"],
            "notes": "DSGVO, AVV, Datenflüsse, Protokollierung.",
        })

    brief = proj.get("brief") or ""
    ucs = _split_use_cases(brief) or ["Auto-Transkription", "Smart Rough Cut", "Auto-Subtitles", "QC-Assist"]

    titles_l = [(s.get("title") or "").strip().lower() for s in plan]
    if "use cases" not in titles_l:
        try:
            es_idx = titles_l.index("executive summary") + 1
        except ValueError:
            es_idx = 1
        plan.insert(es_idx, {"layout_hint":"Content","title":"Use Cases","bullets":[f"- {u}" for u in ucs],"notes":"Überblick über priorisierte Use Cases."})

    have = set((s.get("title") or "").strip().lower() for s in plan)
    for uc in ucs[:5]:
        p_title = f"use case – problem: {uc}".lower()
        s_title = f"use case – lösung/workflow: {uc}".lower()
        if p_title not in have:
            plan.append({"layout_hint":"Content","title":f"Use Case – Problem: {uc}","bullets":["Aktueller Workflow & Pain Points","Zeit-/Kostenfresser, Medienbrüche","Qualitäts-/Compliance-Risiken"],"notes":"Beschreibe Ausgangslage, Prozess-Scope, betroffene Rollen."}); have.add(p_title)
        if s_title not in have:
            plan.append({"layout_hint":"Content","title":f"Use Case – Lösung/Workflow: {uc}","bullets":["Zielbild & automationsgestützter Ablauf","Schnittstellen (NLE/MAM/PAM/Archiv, STT, QC)","Akzeptanzkriterien & Messgrößen (Zeit, Fehler, Kosten)"],"notes":"Skizziere Zielprozess, Tools, Einbettung in vorhandene Systeme."}); have.add(s_title)

    for s in plan:
        if not (s.get("notes") or "").strip():
            s["notes"] = "Hinweise für Presenter."
    return plan

# ------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------
def generate(project_in: Dict[str, Any], slides: Optional[int] = None, modules: Optional[List[str]] = None) -> Dict[str, Any]:
    """Erzeugt einen strukturierten slide_plan aus Outline & Brief (deterministisch, deck-tauglich)."""
    proj = deepcopy(project_in) if project_in else {}
    meta = proj.setdefault("meta", {})

    customer = _norm(proj.get("customer_name"))
    topic    = _norm(proj.get("topic"))
    brief    = _norm(proj.get("brief"))
    outline  = proj.get("outline") or {}

    plan: List[Dict[str, Any]] = []
    plan.append(_title_slide(customer, topic))    # 1) Titelfolie
    plan.extend(_from_outline(outline, brief))    # 2) Inhalte aus Outline

    if slides is not None:
        need = _as_int(slides, 0)
        if need > 0 and len(plan) < need:
            while len(plan) < need:
                plan.append({"layout_hint": "Title and Content","title": "Zusatz / Backup","bullets": ["Reservefolie für Ergänzungen"],"notes": ""})
        elif need > 0 and len(plan) > need:
            plan = plan[:need]

    _ensure_compliance_slide(plan)
    plan = _enrich_pro_plan(proj, plan)
    plan = _ensure_canonical_modules(proj, plan)

    meta["slide_plan"] = plan
    meta["slide_plan_len"] = len(plan)
    meta["k"] = meta.get("k", 6)
    proj["updated_at"] = _now()

    return {"ok": True, "project": proj, "meta": meta}
