# -*- coding: utf-8 -*-
from __future__ import annotations
import json, os, threading, time
from typing import Any, Dict

_DATA_DIR = os.getenv("DATA_DIR", "data")
_TELEMETRY_PATH = os.path.join(_DATA_DIR, "telemetry.jsonl")
_FEEDBACK_PATH  = os.path.join(_DATA_DIR, "feedback.jsonl")
_LOCK = threading.Lock()

def _ensure_dir() -> None:
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR, exist_ok=True)

def _append_jsonl(path: str, payload: Dict[str, Any]) -> None:
    """Immer als Text (UTF-8) schreiben; JSON robust serialisieren."""
    _ensure_dir()
    # harte Felder ergänzen, ohne vorhandene zu überschreiben
    payload = dict(payload)  # defensive copy
    payload.setdefault("ts", int(time.time()))
    # json.dumps robust: notfalls str() als Fallback für un-serialisierbare Werte
    try:
        line = json.dumps(payload, ensure_ascii=False)
    except TypeError:
        safe = {}
        for k, v in payload.items():
            try:
                json.dumps(v)
                safe[k] = v
            except TypeError:
                safe[k] = str(v)
        line = json.dumps(safe, ensure_ascii=False)
    # WICHTIG: Textmodus, nicht "ab"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.write("\n")

def log_event(payload: Dict[str, Any]) -> None:
    """Public API für Analytics-Events (JSONL)."""
    payload = dict(payload)
    payload.setdefault("type", "analytics")
    _append_jsonl(_TELEMETRY_PATH, payload)

def log_feedback(payload: Dict[str, Any]) -> None:
    """Public API für Feedback-Events (JSONL)."""
    payload = dict(payload)
    payload.setdefault("type", "feedback")
    _append_jsonl(_FEEDBACK_PATH, payload)
