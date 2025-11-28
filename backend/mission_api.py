from __future__ import annotations


import json
import time
from pathlib import Path
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import require_api_key

# WICHTIG: plural, damit wir nicht mit alten /mission/{id}-Routen kollidieren
router = APIRouter(
    prefix="/missions",
    tags=["missions"],
    dependencies=[Depends(require_api_key)],
)

MISSION_DIR = Path("data/missions")
MISSION_DIR.mkdir(parents=True, exist_ok=True)


class MissionIn(BaseModel):
    title: str
    client: Optional[str] = None
    briefing: Optional[str] = None
    owner: Optional[str] = None
    status: str = "open"  # open | in_progress | done | archived
    tags: Optional[List[str]] = None


class MissionUpdate(BaseModel):
    title: Optional[str] = None
    client: Optional[str] = None
    briefing: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


def _load_mission(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail="mission not found")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_mission(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.post("/gen")
def mission_gen(body: MissionIn):
    ts = int(time.time())
    name = f"mission-{ts}.json"
    data = {
        "name": name,
        "title": body.title,
        "client": body.client,
        "briefing": body.briefing,
        "owner": body.owner,
        "status": body.status,
        "tags": body.tags or [],
        "created_at": time.time(),
        "updated_at": time.time(),
        "strategies": [],
        "contents": [],
    }
    out = MISSION_DIR / name
    _save_mission(out, data)
    return {"ok": True, "name": name, "path": str(out), "note": "mission saved"}


@router.get("/list")
def mission_list(
    status: Optional[str] = None,
    client: Optional[str] = None,
    q: Optional[str] = None,
):
    items: list[dict[str, Any]] = []
    for p in MISSION_DIR.glob("mission-*.json"):
        m = _load_mission(p)
        if status and m.get("status") != status:
            continue
        if client and m.get("client") != client:
            continue
        if q and q.lower() not in (m.get("title") or "").lower():
            continue
        items.append(
            {
                "name": m.get("name"),
                "title": m.get("title"),
                "client": m.get("client"),
                "status": m.get("status"),
                "owner": m.get("owner"),
                "created_at": m.get("created_at"),
                "updated_at": m.get("updated_at"),
            }
        )
    items.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
    return {"ok": True, "count": len(items), "items": items}


@router.get("/{name}")
def mission_get(name: str):
    path = MISSION_DIR / name
    data = _load_mission(path)
    return {"ok": True, "data": data}


@router.patch("/{name}")
def mission_patch(name: str, body: MissionUpdate):
    path = MISSION_DIR / name
    data = _load_mission(path)
    changed = False
    for field in ["title", "client", "briefing", "owner", "status", "tags"]:
        val = getattr(body, field)
        if val is not None:
            data[field] = val
            changed = True
    if changed:
        data["updated_at"] = time.time()
        _save_mission(path, data)
    return {"ok": True, "data": data}


@router.post("/{name}/attach-strategy")
def mission_attach_strategy(name: str, payload: dict[str, str]):
    strat_name = payload.get("strategy")
    if not strat_name:
        raise HTTPException(status_code=400, detail="strategy name required")
    path = MISSION_DIR / name
    data = _load_mission(path)
    strategies = data.get("strategies") or []
    if strat_name not in strategies:
        strategies.append(strat_name)
    data["strategies"] = strategies
    data["updated_at"] = time.time()
    _save_mission(path, data)
    return {"ok": True, "data": data}


@router.post("/{name}/attach-content")
def mission_attach_content(name: str, payload: dict[str, str]):
    content_name = payload.get("content")
    if not content_name:
        raise HTTPException(status_code=400, detail="content name required")
    path = MISSION_DIR / name
    data = _load_mission(path)
    contents = data.get("contents") or []
    if content_name not in contents:
        contents.append(content_name)
    data["contents"] = contents
    data["updated_at"] = time.time()
    _save_mission(path, data)
    return {"ok": True, "data": data}
