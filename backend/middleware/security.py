import os
from fastapi import FastAPI, Request, HTTPException

def wire_security(app: "FastAPI"):
    api_key = os.getenv("STRATGEN_API_KEY")
    if not api_key:
        return  # offen betreiben
    @app.middleware("http")
    async def api_key_guard(request: Request, call_next):
        # Public GETs dürfen durch (z. B. /exports/list, /exports/latest). Content-POSTs schützen.
        if request.method in ("GET","HEAD","OPTIONS"):
            return await call_next(request)
        provided = request.headers.get("X-API-Key") or request.query_params.get("key")
        if provided != api_key:
            raise HTTPException(status_code=401, detail="invalid api key")
        return await call_next(request)
