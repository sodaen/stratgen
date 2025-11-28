# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from backend.utils_projects import load_project

router = APIRouter(prefix="/projects", tags=["critique"])

@router.post("/{project_id}/critique")
def project_critique(project_id: str):
    pj = load_project(project_id)
    title = pj.get("title") or pj.get("topic") or project_id
    risks = [
        "Annahmen zu Zielgruppen nicht validiert",
        "KPIs nicht mit Sales abgestimmt",
        "Abhängigkeit von 1–2 Kanälen (Risikokonzentration)",
    ]
    counter = [
        "A/B-Tests in Q1 einplanen",
        "Cross-channel Attribution aufsetzen",
        "Content-Refresh alle 6–8 Wochen",
    ]
    assumptions = [
        "CPL < 50 € erreichbar",
        "Website kann Conversions ohne Umbau stemmen",
        "Datenqualität in CRM ausreichend",
    ]
    return {"ok": True, "project": title, "risks": risks, "counterarguments": counter, "assumptions": assumptions}
