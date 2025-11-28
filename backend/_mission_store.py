import os, json, time, uuid, pathlib
from typing import Dict, Any, Optional, List
try:
    import fcntl  # Linux locking
except Exception:
    fcntl = None

DATA_DIR = pathlib.Path(os.getenv("STRATGEN_DATA_DIR", "data")); DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG = DATA_DIR / "missions.jsonl"

def _append(row: Dict[str, Any]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a+") as f:
        if fcntl: fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush(); os.fsync(f.fileno())
        if fcntl: fcntl.flock(f, fcntl.LOCK_UN)

def _iter() -> List[Dict[str, Any]]:
    if not LOG.exists(): return []
    out: List[Dict[str, Any]] = []
    with open(LOG) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: out.append(json.loads(line))
            except: pass
    return out

def create(payload: Dict[str, Any]) -> str:
    mid = "mis-" + uuid.uuid4().hex[:12]
    now = int(time.time())
    _append({"id": mid, "ts": now, "kind": "mission", **payload})
    return mid

def get(mid: str) -> Optional[Dict[str, Any]]:
    for row in reversed(_iter()):
        if row.get("id")==mid: return row
    return None
