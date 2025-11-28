# -*- coding: utf-8 -*-

from __future__ import annotations

import time, json, threading
from typing import Dict
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse

router = APIRouter(tags=["observability"])

# threadsichere, prozesslokale Minimal-Metriken
_METRICS_LOCK = threading.Lock()
_METRICS: Dict[str, float] = {
    "requests_total": 0.0,
    "errors_total": 0.0,
    "inflight": 0.0,
    "request_duration_seconds_sum": 0.0,
}

def _inc(key: str, val: float = 1.0) -> None:
    with _METRICS_LOCK:
        _METRICS[key] = _METRICS.get(key, 0.0) + val

def _dec_inflight() -> None:
    with _METRICS_LOCK:
        _METRICS["inflight"] = max(0.0, _METRICS.get("inflight", 0.0) - 1.0)

def _snapshot() -> Dict[str, float]:
    with _METRICS_LOCK:
        return dict(_METRICS)

class RequestLoggerMiddleware:
    """ASGI-Middleware: misst Latenz, zählt Requests/Errors/Inflight und loggt JSON-Zeilen."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start = time.perf_counter()
        _inc("requests_total", 1.0)
        _inc("inflight", 1.0)
        status = {"code": 200}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message.get("status", status["code"])
            return await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            _inc("errors_total", 1.0)
            raise
        finally:
            dur = time.perf_counter() - start
            with _METRICS_LOCK:
                _METRICS["request_duration_seconds_sum"] = _METRICS.get("request_duration_seconds_sum", 0.0) + dur
            _dec_inflight()
            try:
                log = {
                    "ts": round(time.time(), 3),
                    "path": scope.get("path", "-"),
                    "method": scope.get("method", "-"),
                    "status": status["code"],
                    "dur_ms": int(dur * 1000),
                }
                print(json.dumps(log, separators=(",", ":")))
            except Exception:
                pass

@router.get("/metrics", response_class=PlainTextResponse, tags=["observability"])
async def metrics() -> str:
    s = _snapshot()
    lines = [
        "# HELP stratgen_requests_total Total requests.",
        "# TYPE stratgen_requests_total counter",
        f"stratgen_requests_total {int(s.get('requests_total', 0))}",
        "# HELP stratgen_errors_total Total unhandled exceptions.",
        "# TYPE stratgen_errors_total counter",
        f"stratgen_errors_total {int(s.get('errors_total', 0))}",
        "# HELP stratgen_inflight Inflight requests.",
        "# TYPE stratgen_inflight gauge",
        f"stratgen_inflight {int(s.get('inflight', 0))}",
        "# HELP stratgen_request_duration_seconds_sum Cumulative request time.",
        "# TYPE stratgen_request_duration_seconds_sum counter",
        f"stratgen_request_duration_seconds_sum {s.get('request_duration_seconds_sum', 0.0):.6f}",
    ]
    return "\n".join(lines) + "\n"

@router.get("/debug/ping", response_class=JSONResponse, tags=["observability"])
async def ping():
    return {"ok": True, "ts": time.time()}


from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        resp = await call_next(request)
        resp.headers.setdefault("X-Request-Id", rid)
        return resp
