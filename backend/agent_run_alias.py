import os, requests
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
try:
    from backend._http_retry import request as _http_req
except Exception:
    def _http_req(method, url, timeout=60, **kw): return requests.request(method=method, url=url, timeout=timeout, **kw)

router = APIRouter(prefix="/agent", tags=["agent"])
def _base(): return os.getenv("STRATGEN_INTERNAL_URL","http://127.0.0.1:8011").rstrip("/")
def _target() -> str:
    v = (os.getenv("AGENT_DEFAULT_VERSION","2") or "2").strip()
    return { "0": "/agent/run_v0", "1": "/agent/run_v1" }.get(v, "/agent/run_v2")

@router.post("/run")
async def run_alias(req: Request):
    body = await req.json()
    r = _http_req("post", _base() + _target(), json=body, timeout=180)
    try: data = r.json()
    except Exception: data = {"ok": False, "error": "non-json upstream", "status": r.status_code, "text": r.text}
    return JSONResponse(status_code=r.status_code, content=data)
