from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
from diskcache import Cache
import hashlib, json, threading, time

CACHE_DIR = Path("data/cache"); CACHE_DIR.mkdir(parents=True, exist_ok=True)
_cache: Optional[Cache] = None
_lock = threading.Lock()

def _key(obj: Any) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        s = str(obj)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def get_cache() -> Cache:
    global _cache
    with _lock:
        if _cache is None:
            _cache = Cache(CACHE_DIR)
    return _cache

def cache_get(namespace: str, obj: Any):
    return get_cache().get(namespace + ":" + _key(obj))

def cache_set(namespace: str, obj: Any, value: Any, expire_s: int = 3600):
    get_cache().set(namespace + ":" + _key(obj), value, expire=expire_s)

def cache_clear(prefix: Optional[str] = None) -> int:
    c = get_cache()
    if not prefix:
        n = len(c)
        c.clear()
        return n
    # selektiv löschen
    keys = [k for k in c.iterkeys() if str(k).startswith(prefix)]
    for k in keys: del c[k]
    return len(keys)
