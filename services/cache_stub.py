from functools import lru_cache
try:
    from diskcache import Cache  # optional
    cache = Cache('/tmp/stratgen_cache')
except Exception:
    cache = None

def get(key: str):
    if cache is None: return None
    return cache.get(key)

def set(key: str, value, expire: int = 600):
    if cache is None: return
    cache.set(key, value, expire=expire)
