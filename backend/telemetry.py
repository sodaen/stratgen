import os, json, time, pathlib
from typing import Any, Dict

_TELEMETRY_ON = os.getenv("TELEMETRY_ENABLED", "1") == "1"
_DIR = pathlib.Path("data/telemetry")
_DIR.mkdir(parents=True, exist_ok=True)
_FILE = _DIR / "events.jsonl"

def log_event(kind: str, data: Dict[str, Any]) -> None:
    if not _TELEMETRY_ON: 
        return
    rec = {"ts": int(time.time()), "kind": kind, **data}
    _FILE.write_text("", encoding="utf-8") if not _FILE.exists() else None
    with _FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
