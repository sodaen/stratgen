from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import os, time, requests

try:
    from backend._http_retry import request as _http_req
except Exception:
    def _http_req(method, url, timeout=60, **kw): return requests.request(method=method, url=url, timeout=timeout, **kw)

router = APIRouter(prefix="/agent", tags=["agent"])

def _base():   return os.getenv("STRATGEN_INTERNAL_URL","http://127.0.0.1:8011").rstrip("/")
def _ollama(): return os.getenv("OLLAMA_HOST","http://127.0.0.1:11434").rstrip("/")
def _model():  return os.getenv("LLM_MODEL","mistral")

class AutoReq(BaseModel):
    topic: Optional[str] = None
    mission_id: Optional[str] = None
    k: int = 3
    n_variants: int = 3

@router.post("/autotune")
def autotune(req: AutoReq):
    base = _base()
    topic = req.topic or f"Untitled {int(time.time())}"
    # Preview
    prev = _http_req("get", f"{base}/content/preview_with_sources",
                     params={"topic": f"Short paragraph that mentions: {topic}", "k": req.k},
                     timeout=60).json()
    ctx = prev.get("content","")
    # Draft
    j = _http_req("post", f"{base}/content/generate",
                  json={"prompt": f"Write a crisp paragraph on:\n{topic}\n\nUse this context:\n{ctx}",
                        "max_tokens": 220}, timeout=120).json()
    text = j.get("text") or (j.get("content_map",{}) or {}).get("intro","") or ""

    # Variants
    styles = [
      "Make it more executive-summary style; keep cautious claims.",
      "Make it more actionable; include 2 concrete next steps.",
      "Make it shorter and clearer; remove fluff."
    ][:max(1, req.n_variants)]
    variants = []
    for s in styles:
        r = _http_req("post", f"{_ollama()}/api/generate",
                      json={"model": _model(),
                            "prompt": f"Revise:\n---\n{text}\n---\nInstruction: {s}\nReturn pure text.",
                            "stream": False}, timeout=120).json()
        v = (r or {}).get("response","") or text
        score = _http_req("post", f"{base}/agent/review", json={"text": v}, timeout=60).json()
        total = sum(score.get("scores",{}).values()) if isinstance(score.get("scores"), dict) else 0.0
        variants.append((total, v))

    variants.sort(key=lambda t: t[0], reverse=True)
    best = variants[0][1] if variants else text

    # Project + PPTX
    pid = _http_req("post", f"{base}/projects/save",
                    json={"title": topic, "sections":["Intro","Plan","Next Steps"]}, timeout=60).json().get("project",{}).get("id")
    j = _http_req("post", f"{base}/pptx/render_from_project/{pid}", timeout=90).json()
    pptx_url = j.get("url") or ("/exports/download/" + j.get("path","").split("/")[-1] if j.get("path") else None)

    return {"ok": True, "topic": topic, "project_id": pid, "pptx_url": pptx_url, "variants": len(variants)}
