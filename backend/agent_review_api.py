from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os, json, requests

try:
    from backend._http_retry import request as _http_req
except Exception:
    def _http_req(method, url, timeout=60, **kw): return requests.request(method=method, url=url, timeout=timeout, **kw)

router = APIRouter(prefix="/agent", tags=["agent"])
def _ollama(): return os.getenv("OLLAMA_HOST","http://127.0.0.1:11434").rstrip("/")
def _model():  return os.getenv("LLM_MODEL","mistral")

class ReviewReq(BaseModel):
    text: str
    rubric: Optional[str] = "correctness, clarity, actionability"

@router.post("/review")
def review(req: ReviewReq):
    prompt = (
      "You are a careful reviewer. Score from 0..1 for correctness, clarity, actionability. "
      "Return STRICT JSON: {\"scores\":{\"correctness\":x,\"clarity\":y,\"actionability\":z},"
      "\"suggestions\":[\"...\"]}. Text:\n---\n" + req.text + "\n---"
    )
    r = _http_req("post", f"{_ollama()}/api/generate",
                  json={"model": _model(), "prompt": prompt, "stream": False}, timeout=120)
    raw = (r.json() or {}).get("response","").strip()
    try:
        j = json.loads(raw)
    except Exception:
        j = {"scores": {}, "suggestions": [], "raw": raw}
    return {"ok": True, **j}
