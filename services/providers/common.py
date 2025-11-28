# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, time, hashlib, uuid
from pathlib import Path
from typing import Dict, Any, List

_KEYS_PATH = Path("data/providers/keys.json")

def _file_keys() -> Dict[str, str]:
    if _KEYS_PATH.exists():
        try:
            return json.loads(_KEYS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def get_key(name: str) -> str | None:
    # Env > keys.json
    return os.getenv(name) or _file_keys().get(name)

def missing(required: List[str]) -> List[str]:
    return [k for k in required if not get_key(k)]

def check_config(provider: str, required: List[str]) -> Dict[str, Any]:
    miss = missing(required)
    return {"provider": provider, "configured": len(miss) == 0, "missing": miss}

def normalize_entry(
    customer_name: str,
    title: str,
    text: str,
    source_type: str,
    canonical_url: str | None = None,
    topics: List[str] | None = None,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    ts = int(time.time())
    eid = str(uuid.uuid4())
    h = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()
    return {
        "id": eid,
        "type": "provider",
        "title": title,
        "path": f"provider://{source_type}/{eid}",
        "text": text,
        "tokens": [],
        "topics": topics or [],
        "subtopics": [],
        "customer_name": customer_name,
        "source_type": source_type,
        "canonical_url": canonical_url,
        "pub_date_ts": ts,
        "hash": h,
        "meta": meta or {},
    }
