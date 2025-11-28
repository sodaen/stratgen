# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json, time

ROOT = Path("data/projects")
ROOT.mkdir(parents=True, exist_ok=True)

def _pj(project_id: str) -> Path:
    d = ROOT / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    pid = payload.get("id") or payload.get("project_id") or f"proj-{int(time.time())}"
    d = _pj(pid)
    path = d / "project.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    else:
        existing = {"id": pid, "created_at": time.time()}
    merged = {**existing, **payload, "id": pid, "updated_at": time.time()}
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    path = _pj(project_id) / "project.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def list_projects(limit: Optional[int]=None) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    # Neueste zuerst
    for d in sorted(ROOT.glob("proj-*"), reverse=True):
        pj = d / "project.json"
        if pj.exists():
            try:
                items.append(json.loads(pj.read_text(encoding="utf-8")))
                if limit and len(items) >= limit:
                    break
            except Exception:
                continue
    return items

def append_history(project_id: str, event: str, data: Optional[Dict[str, Any]]=None) -> None:
    d = _pj(project_id)
    p = d / "history.jsonl"
    rec = {"ts": time.time(), "event": event, "data": (data or {})}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\\n")


def load_project(project_id: str):
    return get_project(project_id)
