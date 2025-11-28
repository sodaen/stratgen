
from __future__ import annotations
import json, uuid
from pathlib import Path
from typing import Any

ROOT = Path("data/datasources")
ROOT.mkdir(parents=True, exist_ok=True)

def _path(customer: str) -> Path:
    safe = customer.replace("/", "_")
    return ROOT / f"{safe}.json"

def load(customer: str) -> list[dict[str, Any]]:
    path = _path(customer)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def save(customer: str, items: list[dict[str, Any]]) -> None:
    _path(customer).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def add_entries(customer: str, entries: list[dict[str, Any]]) -> list[str]:
    items = load(customer)
    ids = []
    for e in entries:
        e = dict(e)
        if not e.get("id"):
            e["id"] = str(uuid.uuid4())
        # Normalisieren
        e.setdefault("type", "file")  # "file" | "web"
        e.setdefault("tokens", [])
        e.setdefault("topics", [])
        e.setdefault("subtopics", [])
        items.append(e)
        ids.append(e["id"])
    save(customer, items)
    return ids

def list_entries(customer: str) -> list[dict[str, Any]]:
    return load(customer)

def delete_entry(customer: str, entry_id: str) -> bool:
    items = load(customer)
    new_items = [x for x in items if x.get("id") != entry_id]
    changed = len(new_items) != len(items)
    if changed:
        save(customer, new_items)
    return changed

def get_entries(customer: str, ids: list[str] | None = None) -> list[dict[str, Any]]:
    items = load(customer)
    if not ids:
        return items
    want = set(ids)
    return [x for x in items if x.get("id") in want]
