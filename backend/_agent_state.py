import os, json, time, uuid, pathlib
from typing import Dict, Any, List, Optional

# fcntl ist auf Linux vorhanden; falls nicht, arbeiten wir ohne Lock (Fallback)
try:
    import fcntl  # type: ignore
except Exception:
    fcntl = None  # pragma: no cover

DATA_DIR = pathlib.Path(os.getenv("STRATGEN_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG = DATA_DIR / "agent_runs.jsonl"

def _append(obj: Dict[str, Any]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a+", encoding="utf-8") as f:
        if fcntl:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
            except Exception:
                pass
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass
        if fcntl:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass

def _iter_all() -> List[Dict[str, Any]]:
    if not LOG.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

def new_run(topic: str, params: Dict[str, Any]) -> str:
    rid = "run-" + uuid.uuid4().hex[:12]
    now = int(time.time())
    _append({"id": rid, "ts_start": now, "status": "running", "topic": topic, "params": params})
    return rid

def update_run(rid: str, **kv) -> None:
    kv2 = {"id": rid, **kv, "ts": int(time.time())}
    _append(kv2)

def get_run(rid: str) -> Optional[Dict[str, Any]]:
    items = [x for x in _iter_all() if x.get("id") == rid]
    if not items:
        return None
    base: Dict[str, Any] = {}
    for it in items:
        base.update(it)
    return base

def list_runs(limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
    reduced: Dict[str, Dict[str, Any]] = {}
    for row in _iter_all():
        rid = row.get("id")
        if not rid:
            continue
        reduced[rid] = {**reduced.get(rid, {}), **row}
    vals = list(reduced.values())
    if status:
        vals = [v for v in vals if v.get("status") == status]
    vals.sort(key=lambda v: v.get("ts_start", 0), reverse=True)
    return vals[: limit]
