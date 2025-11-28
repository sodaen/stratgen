# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Any

def _chunk(lst: list, n: int) -> list[list]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def _title(s: dict, suffix: str) -> str:
    t = (s.get("title") or s.get("heading") or "Slide")
    return f"{t} {suffix}"

def expand_to_length(plan: List[Dict[str,Any]], target: int) -> List[Dict[str,Any]]:
    if not isinstance(plan, list): 
        plan = []
    if not target or target <= 0:
        return plan
    out: List[Dict[str,Any]] = []

    # 1) Basis übernehmen + Bullets aufteilen
    for s in plan:
        out.append(s)
        bullets = s.get("bullets") or s.get("items") or []
        if isinstance(bullets, list) and len(bullets) > 6:
            for idx, chunk in enumerate(_chunk(bullets[6:], 6), start=1):
                out.append({
                    "kind": s.get("kind", "content"),
                    "title": _title(s, f"(Fortsetzung {idx})"),
                    "bullets": chunk
                })

    # 2) Fallback, wenn quasi nur Title Slide existiert
    if len(out) < 3:
        topic = None
        for s in plan:
            if s.get("kind") == "title":
                topic = s.get("title") or "Initiative"
                break
        topic = topic or "Initiative"
        skeleton = [
            {"kind":"section","title":"Strategischer Kontext"},
            {"kind":"content","title":"Zielbild & Leitplanken","bullets":["Vision","Ziele (SMART)","Do/Don'ts","Einschränkungen","Erfolgskriterien"]},
            {"kind":"section","title":"Markt & Wettbewerb"},
            {"kind":"content","title":"Market Sizing & Treiber","bullets":["TAM/SAM/SOM grob","Kaufmotive","Saisonalität","Wachstumstreiber","Datenlücken"]},
            {"kind":"section","title":"GTM-Story"},
            {"kind":"content","title":"Kernbotschaften","bullets":["Value Prop 1","Value Prop 2","Differenzierung","Proof Points","CTA"]},
            {"kind":"section","title":"Kanal-/Funnel-Plan"},
            {"kind":"content","title":"Channel Mix (Hypothesen)","bullets":["Search","Social","Email","Events","PR"]},
            {"kind":"content","title":"Funnel & Conversions","bullets":["Awareness → Consideration","Consideration → Purchase","Activation","Retention","Referral"]},
            {"kind":"section","title":"KPIs & Roadmap"},
            {"kind":"content","title":"KPI-Set & Zielwerte","bullets":["Pipeline / MQL/SQL","CLV/CAC","CTR/CPC/ROAS","Win-Rate","Cycle Time"]},
            {"kind":"content","title":"Umsetzung (90 Tage)","bullets":["Meilensteine","Verantwortungen","Risiken","Mitigation","Reporting"]},
        ]
        # wenn es eine Titelfolie gibt, vorn anstellen
        if plan and plan[0].get("kind") == "title":
            out = [plan[0]] + skeleton
        else:
            out = skeleton

    # 3) Deep-dives duplizieren, bis Ziel erreicht
    i = 1
    while len(out) < target:
        for s in list(out):
            if len(out) >= target: break
            if s.get("bullets"):
                out.append({
                    "kind": s.get("kind","content"),
                    "title": _title(s, f"– Deep Dive {i}"),
                    "bullets": s["bullets"]
                })
        i += 1
        if i > 10:  # Sicherheitsnetz
            break

    return out[:target]
