# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Any, Dict, List
import json, time, difflib
from backend.utils_projects import load_project

router = APIRouter(prefix="/projects", tags=["versioning"])

def _vdir(pid: str) -> Path:
    return Path("data/projects") / pid / "versions"

@router.get("/{project_id}/versions")
def list_versions(project_id: str):
    d = _vdir(project_id)
    if not d.exists(): return {"ok": True, "versions": []}
    vs = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        vs.append({"name": p.name, "ts": p.stem, "path": str(p), "size": p.stat().st_size})
    return {"ok": True, "versions": vs}

@router.post("/{project_id}/versions/snapshot")
def snapshot(project_id: str):
    pj = load_project(project_id)
    d = _vdir(project_id); d.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = d / f"{ts}.json"
    path.write_text(json.dumps(pj, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "snapshot": {"ts": ts, "path": str(path)}}

@router.get("/{project_id}/diff")
def diff(project_id: str, ts_a: str = Query(...), ts_b: str = Query(...)):
    d = _vdir(project_id)
    a = (d / f"{ts_a}.json").read_text(encoding="utf-8")
    b = (d / f"{ts_b}.json").read_text(encoding="utf-8")
    diff_lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
    return {"ok": True, "diff": diff_lines}
