from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os, time, requests

try:
    from backend._agent_state import new_run, update_run
except Exception:
    # State optional – darf den Run nicht blockieren
    def new_run(topic: str, params: Dict[str, Any]) -> str: return f"run-{int(time.time())}"
    def update_run(rid: str, **kv): pass

try:
    from backend._http_retry import request as _http_req
except Exception:
    # Fallback ohne Retries
    def _http_req(method: str, url: str, timeout: float = 60, **kw):
        return requests.request(method=method, url=url, timeout=timeout, **kw)

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRunV1Request(BaseModel):
    topic: str
    k: int = 3
    revise: bool = True
    export_pptx: bool = True

def _base() -> str:
    return os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")

def _ollama() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def _telemetry(kind: str, **kw):
    try:
        _http_req("post", f"{_base()}/telemetry/event", json={"kind": kind, **kw}, timeout=10)
    except Exception:
        pass

@router.post("/run_v1")
def run_v1(req: AgentRunV1Request):
    rid = new_run(req.topic, {"k": req.k, "revise": req.revise})
    t0 = time.time()
    _telemetry("agent.start", topic=req.topic, k=req.k, revise=req.revise, run_id=rid)
    update_run(rid, status="running")

    base = _base()

    # 0) RAG seed (tolerant)
    try:
        requests.post(f"{base}/knowledge/embed_local", timeout=10)
    except Exception:
        pass

    # 1) Preview
    r = _http_req("get", f"{base}/content/preview_with_sources",
                  params={"topic": f"Short paragraph that mentions: {req.topic}", "k": req.k},
                  timeout=60)
    prev = r.json() if hasattr(r, "json") else {}
    content = prev.get("content", "")
    sources = prev.get("sources", [])
    _telemetry("agent.preview", topic=req.topic, k=req.k, src=len(sources), run_id=rid, len=len(content))
    update_run(rid, phase="preview", len=len(content))

    # 2) Draft
    payload = {"prompt": f"One paragraph on: {req.topic}\n\nUse this context if helpful:\n{content}",
               "max_tokens": 220}
    r = _http_req("post", f"{base}/content/generate", json=payload, timeout=120)
    j = r.json() if hasattr(r, "json") else {}
    text = j.get("text") or (j.get("content_map", {}) or {}).get("intro", "")
    _telemetry("agent.draft", topic=req.topic, len=len(text), run_id=rid)
    update_run(rid, phase="draft", len=len(text))

    # 3) Revise (optional)
    revised = text
    if req.revise and text:
        try:
            r = _http_req("post", f"{_ollama()}/api/generate",
                          json={"model": os.getenv("LLM_MODEL", "mistral"),
                                "prompt": f"Revise for clarity, actionability, cautious claims:\n---\n{text}",
                                "stream": False},
                          timeout=120)
            revised = (r.json() or {}).get("response") or text
            _telemetry("agent.revise", topic=req.topic, len=len(revised), run_id=rid)
            update_run(rid, phase="revise", len=len(revised))
        except Exception:
            pass

    # 4) Project + PPTX
    project_id: Optional[str] = None
    pptx_url: Optional[str] = None
    pptx_json_url: Optional[str] = None
    export_json: Optional[str] = None

    r = _http_req("post", f"{base}/projects/save",
                  json={"title": req.topic, "sections": ["Intro","Plan","Next Steps"]},
                  timeout=60)
    project_id = (r.json().get("project") or {}).get("id")

    if req.export_pptx and project_id:
        r = _http_req("post", f"{base}/pptx/render_from_project/{project_id}", timeout=90)
        j = r.json()
        pptx_url = j.get("url")
        if not pptx_url and "path" in j:
            pptx_url = f"/exports/download/{j['path'].split('/')[-1]}"
        if pptx_url:
            pptx_json_url = pptx_url + ".json"
            export_json = pptx_json_url

    update_run(rid, status="done", project_id=project_id, pptx_url=pptx_url, export_json=export_json,
               duration_s=round(time.time() - t0, 3))
    _telemetry("agent.done", topic=req.topic, project_id=project_id, has_pptx=bool(pptx_url),
               run_id=rid, duration_s=round(time.time() - t0, 3))

    return {"ok": True, "run_id": rid, "topic": req.topic, "project_id": project_id,
            "pptx_url": pptx_url, "pptx_json_url": pptx_json_url, "export_json": export_json,
            "duration_s": round(time.time() - t0, 3)}
