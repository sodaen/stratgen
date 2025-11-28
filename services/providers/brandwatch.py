# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Any, Optional
from . import common

REQUIRED = ["BRANDWATCH_API_KEY"]

def status() -> Dict[str, Any]:
    return common.check_config("brandwatch", REQUIRED)

def pull_recent(customer_name: str, limit: int = 5, query: Optional[str] = None) -> List[Dict[str, Any]]:
    if not status().get("configured"):
        return []
    out: List[Dict[str, Any]] = []
    for i in range(1, max(0, limit) + 1):
        title = f"Brandwatch mention #{i}" + (f" — {query}" if query else "")
        text = f"Brandwatch (stub) mention {i}. Customer={customer_name}." + (f" Query={query}" if query else "")
        out.append({"title": title, "text": text, "canonical_url": None, "topics": ["social","mention"]})
    return out
