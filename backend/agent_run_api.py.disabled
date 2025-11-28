from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List
import os, time, json, pathlib

from backend._http_retry import request as http_request
from backend.telemetry import log_event

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRunRequest(BaseModel):
    topic: str
    k: int = 5
    revise: bool = True

def _internal_base() -> str:
    return os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")

def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def _llm_model() -> str:
    return os.getenv("LLM_MODEL", "mistral")

def _render_url_fallback(render_json: Dict[str, Any]) -> str | None:
    url = render_json.get("url")
    if url:
        return url
    path = render_json.get("path")
    if path:
        # server exposes /exports/download/{basename}
        name = os.path.basename(path)
        return f"/exports/download/{name}"
    return None

@router.post(
    "/run_v0",
    summary="Agent Run v0.1 (RAG->Draft->(Revise)->PPTX)",
    operation_id="agent_run_v0_1__agent_run_v0",
)
def agent_run_v0(req: AgentRunRequest) -> Dict[str, Any]:
    t0 = time.time()
    base = _internal_base()
    log_event("agent.start", {"topic": req.topic, "k": req.k, "revise": req.revise})

    # 1) Preview + Sources (RAG)
    try:
        r_prev = http_request("GET", f"{base}/content/preview_with_sources",
                              params={"topic": req.topic, "k": req.k}, timeout=60)
        prev = r_prev.json()
    except Exception as e:
        prev = {"content": "", "sources": [], "error": f"preview_error:{e}"}
    content = (prev.get("content") or "")[:4000]
    sources: List[Dict[str, Any]] = prev.get("sources") or []
    log_event("agent.preview", {"topic": req.topic, "k": req.k, "len": len(content), "src": len(sources)})

    # 2) Draft
    prompt = f"Write one crisp paragraph on: {req.topic}\n\nUse this context ONLY if helpful:\n{content}"
    try:
        r_gen = http_request("POST", f"{base}/content/generate",
                             json={"prompt": prompt, "max_tokens": 220}, timeout=90)
        gen = r_gen.json()
    except Exception as e:
        gen = {"error": f"generate_error:{e}"}
    draft = (gen.get("text") or (gen.get("content_map") or {}).get("intro") or "").strip()
    log_event("agent.draft", {"topic": req.topic, "len": len(draft)})

    # 3) Optional: Revise via Ollama
    revised = draft
    if req.revise and draft:
        try:
            rr = http_request("POST", f"{_ollama_host()}/api/generate",
                              json={"model": _llm_model(),
                                    "prompt": "Revise the paragraph: clearer, actionable, cautious.\n\n---\n" + draft,
                                    "stream": False},
                              timeout=90)
            if rr.ok:
                revised = (rr.json().get("response") or draft).strip()
        except Exception:
            pass
    log_event("agent.revise", {"topic": req.topic, "len": len(revised)})

    # 4) Project + PPTX
    try:
        pj = http_request("POST", f"{base}/projects/save",
                          json={"title": req.topic, "sections": ["Intro","Plan","Next Steps"]},
                          timeout=30).json()
        project_id = (pj.get("project") or {}).get("id")
    except Exception as e:
        project_id = None
    pptx_url = None
    pptx_json_url = None
    if project_id:
        try:
            render = http_request("POST", f"{base}/pptx/render_from_project/{project_id}", timeout=120).json()
            pptx_url = _render_url_fallback(render)
            pptx_json_url = render.get("json_url")
        except Exception as e:
            log_event("agent.render.error", {"topic": req.topic, "err": str(e)})
    log_event("agent.done", {"topic": req.topic, "project_id": project_id, "has_pptx": bool(pptx_url)})

    # 5) Run-Summary persistieren
    export_dir = pathlib.Path("data/telemetry")
    export_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    name = f"agent-run-{project_id or 'noid'}-{ts}.json"
    summary = {
        "ok": True, "ts": ts, "topic": req.topic, "k": req.k,
        "sources": sources[:5], "draft": draft, "revised": revised,
        "project_id": project_id, "pptx_url": pptx_url, "pptx_json_url": pptx_json_url,
        "snippet": (content or "")[:200]
    }
    (export_dir / name).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "topic": req.topic,
        "project_id": project_id,
        "pptx_url": pptx_url,
        "pptx_json_url": pptx_json_url,
        "export_json": f"/exports/download/{name}",
        "sources": sources[:3],
        "snippet": (content or "")[:200],
        "duration_s": round(time.time() - t0, 3),
    }

# Convenience: GET-Variante für schnelle Tests
@router.get("/run_v0", summary="Agent Run v0.1 (GET)", operation_id="agent_run_v0_1_get__agent_run_v0")
def agent_run_v0_get(topic: str, k: int = 3, revise: bool = True):
    return agent_run_v0(AgentRunRequest(topic=topic, k=k, revise=revise))

# --- agent run v1 (safe append) ---
from typing import Optional
try:
    from fastapi import APIRouter
    from pydantic import BaseModel
    import os, time, requests
    from backend._agent_state import new_run, update_run
    try:
        from backend._http_retry import request as _http_req
    except Exception:
        import requests as _http_req  # fallback: hat keine Retries, aber bricht nicht
except Exception as _e:
    raise

# falls router nicht existiert (shouldn't), neu anlegen
if "router" not in globals():
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
    try:
        r = _http_req("get", f"{base}/content/preview_with_sources",
                      params={"topic": f"Short paragraph that mentions: {req.topic}", "k": req.k},
                      timeout=60)
        prev = r.json() if hasattr(r, "json") else r
        content = prev.get("content", "") if isinstance(prev, dict) else ""
        sources = prev.get("sources", []) if isinstance(prev, dict) else []
        _telemetry("agent.preview", topic=req.topic, k=req.k, src=len(sources), run_id=rid, len=len(content))
        update_run(rid, phase="preview", len=len(content))
    except Exception as e:
        update_run(rid, status="error", error=f"preview: {e}")
        raise

    # 2) Draft
    try:
        payload = {"prompt": f"One paragraph on: {req.topic}\n\nUse this context if helpful:\n{content}",
                   "max_tokens": 220}
        r = _http_req("post", f"{base}/content/generate", json=payload, timeout=120)
        j = r.json() if hasattr(r, "json") else {}
        text = j.get("text") or (j.get("content_map", {}) or {}).get("intro", "")
        _telemetry("agent.draft", topic=req.topic, len=len(text), run_id=rid)
        update_run(rid, phase="draft", len=len(text))
    except Exception as e:
        update_run(rid, status="error", error=f"draft: {e}")
        raise

    # 3) Revise (optional, tolerant)
    revised = text
    if req.revise and text:
        try:
            r = _http_req("post", f"{_ollama()}/api/generate",
                          json={"model": os.getenv("LLM_MODEL", "mistral"),
                                "prompt": f"Revise for clarity, actionability, cautious claims:\n---\n{text}",
                                "stream": False},
                          timeout=120)
            revised = r.json().get("response") or text
            _telemetry("agent.revise", topic=req.topic, len=len(revised), run_id=rid)
            update_run(rid, phase="revise", len=len(revised))
        except Exception:
            # Revision ist nice-to-have
            pass

    # 4) Project + PPTX
    project_id: Optional[str] = None
    pptx_url: Optional[str] = None
    pptx_json_url: Optional[str] = None
    export_json: Optional[str] = None
    try:
        r = _http_req("post", f"{base}/projects/save",
                      json={"title": req.topic, "sections": ["Intro", "Plan", "Next Steps"]},
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
    except Exception as e:
        update_run(rid, status="error", error=f"export: {e}", project_id=project_id)
        raise

    return {"ok": True, "run_id": rid, "topic": req.topic, "project_id": project_id,
            "pptx_url": pptx_url, "pptx_json_url": pptx_json_url, "export_json": export_json,
            "duration_s": round(time.time() - t0, 3)}
# --- /agent run v1 ---
