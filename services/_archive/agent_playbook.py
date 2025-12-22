# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Optional
import time

# fester 5-Schritte-Plan für das UI
PLAYBOOK: List[Dict[str, Any]] = [
    {
        "code": "collect_assets",
        "label": "Assets & Quellen sammeln",
        "weight": 15,
        "desc": "Manifest, Uploads, Provider, Projekt-Metadaten einsammeln",
    },
    {
        "code": "extract_facts",
        "label": "Fakten & Tabellen extrahieren",
        "weight": 15,
        "desc": "CSV/XLSX/PDF → facts/charts",
    },
    {
        "code": "build_plan",
        "label": "Strategische Struktur bauen",
        "weight": 25,
        "desc": "Outline aus Projekt + Knowledge + Facts",
    },
    {
        "code": "compose_slides",
        "label": "Slides & Inhalte generieren",
        "weight": 30,
        "desc": "NLG / RAG / Templates",
    },
    {
        "code": "review_export",
        "label": "Review & Export",
        "weight": 15,
        "desc": "Critic / Telemetry / PPTX",
    },
]


def get_default_playbook() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for order, step in enumerate(PLAYBOOK, start=1):
        item = dict(step)
        item["order"] = order
        out.append(item)
    return out


def build_tasks_for_mission(
    mission_id: int,
    project: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ts = int(time.time())
    tasks: List[Dict[str, Any]] = []
    for idx, step in enumerate(PLAYBOOK, start=1):
        tasks.append(
            {
                "mission_id": mission_id,
                "title": step["label"],
                "status": "todo",
                "kind": step["code"],
                "payload": {
                    "step_code": step["code"],
                    "project": project or {},
                    "idx": idx,
                },
                "due_ts": 0,
                "created_at": ts,
                "updated_at": ts,
            }
        )
    return tasks
