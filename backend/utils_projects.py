# -*- coding: utf-8 -*-
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR = Path("data")
PJ_DIR = DATA_DIR / "projects"

def _pj_json_path(project_id: str) -> Path:
    return PJ_DIR / project_id / "project.json"

def load_project(project_id: str) -> Dict[str, Any]:
    # Try via backend.projects_api
    try:
        from backend.projects_api import get_project  # type: ignore
        pj = get_project(project_id)  # may raise
        if isinstance(pj, dict): return pj
    except Exception:
        pass
    # Fallback: JSON on disk
    p = _pj_json_path(project_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # minimal shell
    return {"id": project_id, "title": f"Project {project_id}", "outline": {"sections": []}}


def save_project(pj: Dict[str, Any]) -> Dict[str, Any]:
    # Versuche primären Pfad über backend.projects_api.save_project
    try:
        from backend.projects_api import save_project as _save  # type: ignore
        res = _save(pj)
        # Fälle:
        # 1) Endpoint-ähnlich: {"ok": True, "project": {...}}
        if isinstance(res, dict) and res.get("ok") and res.get("project"):
            return res
        # 2) Interner Helper: {..., "id": "..."} (rohes Projekt)
        if isinstance(res, dict) and res.get("id"):
            return {"ok": True, "project": res}
        # 3) Sonst irgendwas -> trotzdem einpacken
        return {"ok": True, "project": res if isinstance(res, dict) else pj}
    except Exception:
        pass
    # Fallback: lokal auf Disk persistieren
    import json, time
    pid = pj.get("id") or f"proj-{int(time.time())}"
    pj["id"] = pid
    path = _pj_json_path(pid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pj, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "project": pj}
