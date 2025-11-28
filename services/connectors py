# services/connectors.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os, hashlib, time

# Deine vorhandenen Services
from services.datasource_store import add_entries

def _fetch_url(url: str) -> Dict[str, Any]:
    """Sehr rudimentär: HTTP-GET + Plaintext. In echt: Boilerplate-Removal, Readability, HTML→Text, Datum, Autor."""
    import requests
    r = requests.get(url, timeout=20)
    txt = r.text or ""
    return {
        "text": txt,
        "title": None,
        "canonical_url": url,
        "pub_date_ts": int(time.time()),
        "hash": hashlib.sha1(url.encode()).hexdigest(),
        "source_type": "web",
    }

def _fetch_brandwatch(query: str, limit: int) -> List[Dict[str, Any]]:
    # TODO: echte API-Calls; hier nur ein Stub
    if not os.getenv("BW_API_KEY"):
        return []
    return [{
        "text": f"Brandwatch-Stub zu '{query}'",
        "title": "Brandwatch Sample",
        "canonical_url": None,
        "pub_date_ts": int(time.time()),
        "hash": hashlib.sha1(f"bw:{query}".encode()).hexdigest(),
        "source_type": "api_brandwatch",
    }]

def _fetch_talkwalker(query: str, limit: int) -> List[Dict[str, Any]]:
    if not os.getenv("TW_API_KEY"):
        return []
    return [{
        "text": f"Talkwalker-Stub zu '{query}'",
        "title": "Talkwalker Sample",
        "canonical_url": None,
        "pub_date_ts": int(time.time()),
        "hash": hashlib.sha1(f"tw:{query}".encode()).hexdigest(),
        "source_type": "api_talkwalker",
    }]

def _fetch_statista(query: str, limit: int) -> List[Dict[str, Any]]:
    if not os.getenv("STATISTA_API_KEY"):
        return []
    return [{
        "text": f"Statista-Stub zu '{query}' (Kennzahlen, Marktvolumina, Quellenhinweise)",
        "title": "Statista Sample",
        "canonical_url": None,
        "pub_date_ts": int(time.time()),
        "hash": hashlib.sha1(f"statista:{query}".encode()).hexdigest(),
        "source_type": "api_statista",
    }]

def run_crawl(customer_name: str, limit: int = 25,
              include_kinds: Optional[list[str]] = None,
              connectors: Optional[list[str]] = None) -> Dict[str, Any]:
    """
    Lädt aus unterschiedlichen Quellen. In echt würdest du hier:
      - registrierte 'url' Einträge lesen
      - je nach 'connectors' API-Calls machen (Brandwatch/Talkwalker/Statista)
      - alles in deinen Store ingesten
    """
    include_kinds = include_kinds or ["url","api","file_id"]
    connectors = connectors or []

    entries: List[Dict[str, Any]] = []

    # Beispiel: feste Test-URL (ersetzbar durch echte Registry-Abfrage)
    if "url" in include_kinds:
        try:
            entries.append(_fetch_url("https://example.com"))
        except Exception:
            pass

    # API-Connectoren
    if "brandwatch" in connectors:
        entries += _fetch_brandwatch(query="Marke Wettbewerb", limit=limit//3 or 5)
    if "talkwalker" in connectors:
        entries += _fetch_talkwalker(query="Social Signals", limit=limit//3 or 5)
    if "statista" in connectors:
        entries += _fetch_statista(query="Marktvolumen 2024 DACH", limit=limit//3 or 5)

    # alles mit Kundenname versehen und ablegen
    for e in entries:
        e.setdefault("customer_name", customer_name)
        e.setdefault("tokens", [])
        e.setdefault("topics", [])
        e.setdefault("subtopics", [])

    ids = add_entries(customer_name, entries)
    return {"fetched": len(ids), "ids": ids}

