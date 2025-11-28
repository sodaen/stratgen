from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os, time, requests

try:
    from backend._mission_store import get as mission_get
except Exception:
    mission_get = lambda _id: None

try:
    from backend._agent_state import new_run, update_run
except Exception:
    def new_run(topic, params): return f"run-{int(time.time())}"
    def update_run(rid, **kv): pass

try:
    from backend._http_retry import request as _http_req
except Exception:
    def _http_req(method, url, timeout=60, **kw): return requests.request(method=method, url=url, timeout=timeout, **kw)

router = APIRouter(prefix="/agent", tags=["agent"])

class RunV2Req(BaseModel):
    topic: Optional[str] = None
    mission_id: Optional[str] = None
    k: int = 3
    revise: bool = True
    export_pptx: bool = True

def _base() -> str: return os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
def _ollama() -> str: return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
def _model() -> str: return os.getenv("LLM_MODEL", "mistral")

@router.post("/run_v2")
def run_v2(req: RunV2Req):
    # Resolve topic from mission if provided
    topic = req.topic
    if not topic and req.mission_id:
        m = mission_get(req.mission_id) or {}
        parts = [m.get("objective","")]
        if m.get("audience"): parts.append(f"For: {m['audience']}")
        if m.get("voice"): parts.append(f"Voice: {m['voice']}")
        if m.get("constraints"): parts.append(f"Constraints: {m['constraints']}")
        topic = " | ".join([p for p in parts if p]) or "Untitled Mission"
    topic = topic or "Untitled"

    rid = new_run(topic, {"k": req.k, "revise": req.revise, "v": 2})
    t0 = time.time(); base = _base()

    # Preview
    prev = _http_req("get", f"{base}/content/preview_with_sources",
                     params={"topic": f"Short paragraph that mentions: {topic}", "k": req.k},
                     timeout=60).json()
    content = prev.get("content",""); sources = prev.get("sources",[])
    update_run(rid, phase="preview", src=len(sources), len=len(content))

    # Draft
    payload = {"prompt": f"Write a crisp paragraph on:\n{topic}\n\nUse this context if helpful:\n{content}",
               "max_tokens": 220}
    j = _http_req("post", f"{base}/content/generate", json=payload, timeout=120).json()
    text = j.get("text") or (j.get("content_map",{}) or {}).get("intro","")
    update_run(rid, phase="draft", len=len(text))

    # Revise (optional)
    revised = text
    if req.revise and text:
        try:
            r = _http_req("post", f"{_ollama()}/api/generate",
                          json={"model": _model(),
                                "prompt": f"Revise for clarity, actionability, cautious claims:\n---\n{text}",
                                "stream": False}, timeout=120)
            revised = (r.json() or {}).get("response") or text
            update_run(rid, phase="revise", len=len(revised))
        except Exception:
            pass

    # Project + PPTX
    project_id = _http_req("post", f"{base}/projects/save",
                           json={"title": topic, "sections":["Intro","Plan","Next Steps"]},
                           timeout=60).json().get("project",{}).get("id")

    pptx_url = None; pptx_json_url = None; export_json = None
    if req.export_pptx and project_id:
        j = _http_req("post", f"{base}/pptx/render_from_project/{project_id}", timeout=90).json()
        pptx_url = j.get("url") or ("/exports/download/" + j.get("path","").split("/")[-1] if j.get("path") else None)
        if pptx_url:
            pptx_json_url = pptx_url + ".json"
            export_json = pptx_json_url

    update_run(rid, status="done", project_id=project_id, pptx_url=pptx_url, export_json=export_json,
               duration_s=round(time.time()-t0,3))

    return {"ok": True, "run_id": rid, "topic": topic, "project_id": project_id,
            "pptx_url": pptx_url, "pptx_json_url": pptx_json_url, "export_json": export_json,
            "duration_s": round(time.time()-t0,3)}
