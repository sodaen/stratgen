
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Any
from pathlib import Path
import uuid, time, json

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "sources" / "sources.json"

class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    type: str  # "file" | "url" | "sheet" | ...
    url: Optional[str] = None
    file_path: Optional[str] = None
    tags: list[str] = []
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    note: Optional[str] = None
    created_at: float = Field(default_factory=lambda: time.time())
    meta: dict[str, Any] = {}

def _load() -> list[Source]:
    if not DB.exists(): return []
    try:
        return [Source(**x) for x in json.loads(DB.read_text(encoding="utf-8"))]
    except Exception:
        return []

def _save(items: list[Source]):
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps([x.model_dump() for x in items], ensure_ascii=False, indent=2), encoding="utf-8")

def add_source(src: Source) -> Source:
    items=_load(); items.append(src); _save(items); return src

def list_sources(customer_name: Optional[str]=None) -> list[dict]:
    items=_load()
    if customer_name:
        items=[x for x in items if x.customer_name==customer_name]
    return [x.model_dump() for x in items]

def remove_source(id: str) -> bool:
    items=_load()
    left=[]; removed=False
    for it in items:
        if it.id==id: removed=True
        else: left.append(it)
    if removed: _save(left)
    return removed
