import os, time, requests
from typing import Any, Dict, Optional

_MAX = int(os.getenv("HTTP_RETRY_MAX", "3"))
_BACKOFF = float(os.getenv("HTTP_RETRY_BACKOFF", "0.5"))

def _sleep(t: float):  # tiny wrapper (easier to test/patch)
    time.sleep(t)

def request(method: str, url: str, *, timeout: float = 60, **kw) -> requests.Response:
    last_ex: Optional[Exception] = None
    for attempt in range(1, _MAX + 1):
        try:
            r = requests.request(method.upper(), url, timeout=timeout, **kw)
            # retry on >=500
            if r.status_code >= 500 and attempt < _MAX:
                raise RuntimeError(f"server_status_{r.status_code}")
            return r
        except Exception as ex:
            last_ex = ex
            if attempt >= _MAX:
                break
            _sleep(_BACKOFF * attempt)
    if isinstance(last_ex, Exception):
        raise last_ex
    raise RuntimeError("request_failed")
