
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import json, csv

def load_upload(file_path: str|Path) -> Dict[str, Any]:
    p = Path(file_path)
    if not p.exists(): return {"ok": False, "error": "not_found"}
    if p.suffix.lower() in [".json"]:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {"ok": True, "facts": data}
    if p.suffix.lower() in [".csv"]:
        rows = list(csv.DictReader(p.read_text(encoding="utf-8").splitlines()))
        return {"ok": True, "facts": {"table": rows}}
    # Fallback: Rohtext
    return {"ok": True, "facts": {"text": p.read_text(encoding="utf-8", errors="ignore")}}

def load_url(url: str) -> Dict[str, Any]:
    # Platzhalter: echte HTTP-Fetcher später; jetzt nur Marker
    return {"ok": True, "facts": {"source_url": url}}

def load_brandwatch(query: str, token: Optional[str]=None) -> Dict[str, Any]:
    # Stub – echte API später
    return {"ok": True, "facts": {"brandwatch_query": query, "insights": []}}

def load_talkwalker(query: str, token: Optional[str]=None) -> Dict[str, Any]:
    return {"ok": True, "facts": {"talkwalker_query": query, "insights": []}}

def load_statista(topic: str, token: Optional[str]=None) -> Dict[str, Any]:
    return {"ok": True, "facts": {"statista_topic": topic, "charts": []}}

def merge_facts(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {"text_blobs": [], "tables": [], "metrics": {}, "insights": [], "sources": []}
    for it in items:
        if not it or not it.get("ok"): continue
        f = it.get("facts") or {}
        if isinstance(f, dict):
            if "text" in f: merged["text_blobs"].append(f["text"])
            if "table" in f: merged["tables"].append(f["table"])
            if "insights" in f: merged["insights"] += f["insights"]
            if "charts" in f: merged["insights"] += [{"chart": c} for c in f["charts"]]
            if "metrics" in f: merged["metrics"].update(f["metrics"])
            if "source_url" in f: merged["sources"].append(f["source_url"])
            if "brandwatch_query" in f or "talkwalker_query" in f or "statista_topic" in f:
                merged["sources"].append(f)
        elif isinstance(f, list):
            merged["text_blobs"] += [str(x) for x in f]
    return merged
