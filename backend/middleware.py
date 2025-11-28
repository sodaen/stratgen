import time, uuid, json, logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("stratgen")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.time()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            dur = round((time.time()-start)*1000, 1)
            log = {
                "rid": rid,
                "path": request.url.path,
                "status": getattr(response, "status_code", -1),
                "ms": dur,
                "method": request.method,
            }
            logger.info(json.dumps(log))
