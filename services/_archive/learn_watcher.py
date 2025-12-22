


# === auto-managed: learn_watcher core ===
from __future__ import annotations
import threading, time, traceback
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_OK = True
except Exception:
    WATCHDOG_OK = False

INGEST_EXT = {".pptx", ".ppt"}
WATCH_DIRS = [Path("data/raw"), Path("data/exports"), "data/knowledge/derived"]

def _should_ingest(p: Path) -> bool:
    try:
        return p.suffix.lower() in INGEST_EXT and p.is_file()
    except Exception:
        return False

def _safe_ingest(p: Path):
    try:
        from services.learn import ingest_exports
        ingest_export(str(p))
        print(f"[learn] ingested: {p}")
    except Exception as e:
        print(f"[learn] ingest error: {p} :: {e}")

def rescan_all() -> dict:
    """Manueller Rescan beider Verzeichnisse."""
    scanned, queued = 0, 0
    for d in WATCH_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        for p in d.rglob("*"):
            scanned += 1
            if _should_ingest(p):
                queued += 1
                _safe_ingest(p)
    return {"ok": True, "scanned": scanned, "queued": queued}

# Live-Watcher (optional)
class _Handler(FileSystemEventHandler):
    def on_created(self, event):
        try:
            p = Path(event.src_path)
            if _should_ingest(p):
                _safe_ingest(p)
        except Exception as e:
            print("[learn] handler error:", e)

_observer = None

def start_watcher():
    global _observer
    if not WATCHDOG_OK:
        print("[learn] watchdog nicht verfügbar – Rescan per API nutzen.")
        return
    if _observer is not None:
        return
    obs = Observer()
    for d in WATCH_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        obs.schedule(_Handler(), str(d), recursive=True)
    obs.daemon = True
    obs.start()
    _observer = obs
    print("[learn] watcher gestartet für:", ", ".join(str(x) for x in WATCH_DIRS))
# === auto-managed end ===
