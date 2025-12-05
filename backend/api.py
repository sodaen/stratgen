import os, importlib, pkgutil, logging, traceback
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

APP_ENV = os.getenv("APP_ENV", "prod")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger("stratgen.api")

from fastapi.routing import APIRoute

def _unique_op_id(route: APIRoute):
    # name + path als operation_id, vermeidet Duplikate über mehrere Router
    return f"{route.name}_{route.path.replace('/', '_')}"

app = FastAPI(title="stratgen", version=os.getenv("_VERSION","dev"), generate_unique_id_function=_unique_op_id)

# CORS (optional via ENV)
origins = os.getenv("STRATGEN_CORS_ORIGINS", "")
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Static mount
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
static_dir = os.path.abspath(static_dir)
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

def _safe_include(module_name: str) -> bool:
    """
    Importiert ein Modul und hängt `router` an.
    Gibt True zurück, wenn erfolgreich eingebunden.
    """
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        log.warning("Import failed for %s\n%s", module_name, traceback.format_exc())
        return False

    router = getattr(mod, "router", None)
    if router is None:
        # kein Router – ok, einfach weiter
        return False
    try:
        app.include_router(router)
        log.info("Included router from %s", module_name)
        return True
    except Exception:
        log.warning("include_router failed for %s\n%s", module_name, traceback.format_exc())
        return False

def _autodiscover():
    # Alle backend.* Module scannen
    # 1) direct *_api.py unter backend/
    # 2) alles in backend.routers.*
    imported = 0
    # 1) backend.* direkt
    import backend as _backend  # noqa
    for m in pkgutil.iter_modules(_backend.__path__, prefix="backend."):
        name = m.name
        # nur *_api oder routers.*
        if name.endswith("_api") or name.startswith("backend.routers."):
            if _safe_include(name):
                imported += 1
    return imported

# Erst Auto-Discovery laufen lassen
count = _autodiscover()
log.info("Auto-discovered routers: %d", count)

# Kritische Router explizit (falls Auto-Discovery sie nicht erwischt)
for forced in (
    "backend.projects_api",
    "backend.exports_api",
    "backend.pptx_api",
    "backend.images_api",     # dein Bild-Generator
):
    _safe_include(forced)

@app.get("/health")
def health():
    # minimal, damit Health IMMER geht – selbst wenn Router schief stehen
    styles = {"brand": True, "minimal": True}
    return {"status": "ok", "ts": int(__import__("time").time()),
            "env": {"APP_ENV": APP_ENV}, "styles": styles}

# Fallback-Health auf _health
app.get("/_health")(health)

# --- guard/diag (idempotent) ---
import os, logging, traceback
try:
    from fastapi import Request
except Exception:
    Request = None

_REQUIRED_ROUTERS = {
    "backend.projects_api",
    "backend.exports_api",
    "backend.pptx_api",
    "backend.images_api",
}

def _loaded_endpoint_modules(app):
    mods = set()
    try:
        for r in getattr(app, "routes", []):
            ep = getattr(r, "endpoint", None)
            mname = getattr(ep, "__module__", None)
            if mname:
                mods.add(mname)
    except Exception:
        pass
    return mods

def _duplicate_operation_ids(app):
    ids, dups = set(), set()
    try:
        for r in getattr(app, "routes", []):
            oid = getattr(r, "operation_id", None)
            if not oid:
                continue
            if oid in ids:
                dups.add(oid)
            else:
                ids.add(oid)
    except Exception:
        pass
    return sorted(dups)

@app.get("/ops/diag")
def ops_diag():
    mods = _loaded_endpoint_modules(app)
    missing = sorted([m for m in _REQUIRED_ROUTERS if m not in mods])
    dups = _duplicate_operation_ids(app)
    return {
        "ok": True,
        "env": {
            "APP_ENV": os.getenv("APP_ENV"),
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
            "LLM_MODEL": os.getenv("LLM_MODEL"),
            "STRATGEN_MODE": os.getenv("STRATGEN_MODE"),
        },
        "routes_total": len(getattr(app, "routes", [])),
        "required_missing": missing,
        "duplicates": dups,
        "loaded_modules": sorted(list(mods))[:200],
    }

try:
    _mods = _loaded_endpoint_modules(app)
    _miss = [m for m in _REQUIRED_ROUTERS if m not in _mods]
    if _miss:
        logging.getLogger("stratgen.api").warning("GUARD: missing routers: %s", _miss)
except Exception as _e:
    logging.getLogger("stratgen.api").warning("GUARD setup issue: %s", _e)
    traceback.print_exc()
# --- end guard/diag ---

# --- preview/generate overrides (remove old routes, install new) ---
from fastapi import Query, Body
from fastapi.routing import APIRoute
from typing import List, Dict, Any
import os, requests, pathlib

def _llm_generate(prompt: str, max_tokens: int = 220) -> str:
    prov = os.getenv("LLM_PROVIDER", "ollama")
    if prov == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("LLM_MODEL", "mistral")
        try:
            r = requests.post(f"{host}/api/generate",
                              json={"model": model, "prompt": prompt, "stream": False},
                              timeout=60)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception:
            return ""
    return ""

def _rag_context(q: str, k: int = 5) -> List[Dict[str, Any]]:
    try:
        internal = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
        r = requests.get(f"{internal}/knowledge/search_semantic",
                         params={"q": q, "k": k}, timeout=30)
        r.raise_for_status()
        hits = r.json().get("_hits") or r.json().get("hits") \
            or r.json().get("results") or r.json().get("items") \
            or r.json().get("sources") or []
        norm = []
        for h in hits:
            if isinstance(h, dict):
                path = h.get("path") or h.get("file") or h.get("key")
                score = h.get("score") or h.get("similarity") or 0
                if path:
                    norm.append({"path": path, "score": score})
        return norm[:k]
    except Exception:
        return []

def _read_snippets(paths: List[Dict[str, Any]], limit_chars: int = 800) -> str:
    out = []
    base = pathlib.Path().resolve()
    for hit in paths:
        p = hit["path"]
        p = pathlib.Path(p)
        if not p.is_absolute():
            p = base / p
        try:
            txt = pathlib.Path(p).read_text(encoding="utf-8", errors="ignore")
            if txt:
                out.append(f"[{hit.get('score',0):.3f}] {txt.strip()[:limit_chars]}")
        except Exception:
            continue
    return "\n\n".join(out)

def _install_preview_overrides(_app):
    # 1) vorhandene Routen entfernen
    targets = {
        ("/content/preview", "GET"), ("/content/preview", "POST"),
        ("/content/preview_with_sources", "GET"), ("/content/preview_with_sources", "POST"),
        ("/content/generate", "POST")
    }
    new_routes = []
    for r in list(_app.router.routes):
        if isinstance(r, APIRoute) and any((r.path, m) in targets for m in r.methods):
            continue
        new_routes.append(r)
    _app.router.routes = new_routes

    # 2) neue Implementierungen registrieren
    @_app.get("/content/preview", tags=["content"])
    def _preview(topic: str = Query(..., description="Topic/prompt for preview"),
                 k: int = Query(3, ge=1, le=50)):
        sources = _rag_context(topic, k)
        ctx = _read_snippets(sources, 800) if sources else ""
        prompt = f"Write a short, self-contained paragraph about: {topic}."
        if ctx:
            prompt += f"\n\nUse this context where relevant:\n{ctx}"
        text = _llm_generate(prompt) or f"Outline:\n- Einordnung: Rahmen für: {topic}"
        return {"ok": True, "topic": topic, "content": text, "sources": sources}

    @_app.get("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources(topic: str = Query(...), k: int = Query(3, ge=1, le=50)):
        return _preview(topic=topic, k=k)

    @_app.post("/content/preview", tags=["content"])
    def _preview_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview(topic=topic, k=k)

    @_app.post("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview(topic=topic, k=k)

    @_app.post("/content/generate", tags=["content"])
    def _generate(payload: Dict[str, Any] = Body(...)):
        prompt = (payload.get("prompt") or payload.get("topic") or "").strip()
        max_tokens = int(payload.get("max_tokens", 220))
        text = _llm_generate(prompt, max_tokens=max_tokens)
        # kompatibel zum bisherigen Shape + zusätzlich 'text'
        return {
            "ok": True,
            "text": text,
            "content_map": {
                "intro": text,
                "body": "",
                "outro": "",
                "bullets": [],
                "citations": [],
            },
            "sources": []
        }


# RAG API Router
try:
    from backend.rag_api import router as _rag_router
    app.include_router(_rag_router)
    log.info("RAG API router loaded")
except Exception as e:
    log.warning(f"RAG API router failed: {e}")

# Knowledge Admin API
try:
    from backend import knowledge_admin_api
    app.include_router(knowledge_admin_api.router)
    log.info("knowledge_admin_api router registered")
except Exception as e:
    log.warning(f"knowledge_admin_api failed: {e}")

# Knowledge Analytics API
try:
    from backend import knowledge_analytics_api
    app.include_router(knowledge_analytics_api.router)
    log.info("knowledge_analytics_api router registered")

# nach allen include_router()-Aufrufen ausführen
try:
    _install_preview_overrides(app)
except Exception as _e:
    # Fail closed (keinen Crash riskieren)
    pass
# --- /overrides ---

# --- sprint1 quick wins: preview ttl-cache + openapi operationId dedup ---
from fastapi import Query, Body
from fastapi.routing import APIRoute
from typing import List, Dict, Any
import os, requests, pathlib, threading, time

# ---- LLM + RAG helpers (reuse-safe) ----
def _llm_generate(prompt: str, max_tokens: int = 220) -> str:
    prov = os.getenv("LLM_PROVIDER", "ollama")
    if prov == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("LLM_MODEL", "mistral")
        try:
            r = requests.post(f"{host}/api/generate",
                              json={"model": model, "prompt": prompt, "stream": False},
                              timeout=60)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception:
            return ""
    return ""

def _rag_context(q: str, k: int = 5) -> List[Dict[str, Any]]:
    try:
        internal = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
        r = requests.get(f"{internal}/knowledge/search_semantic",
                         params={"q": q, "k": k}, timeout=30)
        r.raise_for_status()
        hits = r.json().get("_hits") or r.json().get("hits") \
            or r.json().get("results") or r.json().get("items") \
            or r.json().get("sources") or []
        norm = []
        for h in hits:
            if isinstance(h, dict):
                path = h.get("path") or h.get("file") or h.get("key")
                score = h.get("score") or h.get("similarity") or 0
                if path:
                    norm.append({"path": path, "score": score})
        return norm[:k]
    except Exception:
        return []

def _read_snippets(paths: List[Dict[str, Any]], limit_chars: int = 800) -> str:
    out = []
    base = pathlib.Path().resolve()
    for hit in paths:
        p = hit["path"]
        p = pathlib.Path(p)
        if not p.is_absolute():
            p = base / p
        try:
            txt = pathlib.Path(p).read_text(encoding="utf-8", errors="ignore")
            if txt:
                out.append(f"[{hit.get('score',0):.3f}] {txt.strip()[:limit_chars]}")
        except Exception:
            continue
    return "\n\n".join(out)

# ---- TTL cache for preview ----
_PREVIEW_CACHE_TTL = int(os.getenv("PREVIEW_CACHE_TTL", "60"))
_preview_cache: Dict[tuple, tuple] = {}
_preview_lock = threading.Lock()

def _install_preview_overrides(_app):
    # remove old preview/generate routes
    targets = {
        ("/content/preview", "GET"), ("/content/preview", "POST"),
        ("/content/preview_with_sources", "GET"), ("/content/preview_with_sources", "POST"),
        ("/content/generate", "POST")
    }
    new_routes = []
    for r in list(_app.router.routes):
        if isinstance(r, APIRoute) and any((r.path, m) in targets for m in r.methods):
            continue
        new_routes.append(r)
    _app.router.routes = new_routes

    def _preview_impl(topic: str, k: int):
        key = (topic, int(k))
        now = time.time()
        with _preview_lock:
            ts_resp = _preview_cache.get(key)
            if ts_resp and (now - ts_resp[0] < _PREVIEW_CACHE_TTL):
                return ts_resp[1]
        sources = _rag_context(topic, k)
        ctx = _read_snippets(sources, 800) if sources else ""
        prompt = f"Write a short, self-contained paragraph about: {topic}."
        if ctx:
            prompt += f"\n\nUse this context where relevant:\n{ctx}"
        text = _llm_generate(prompt) or f"Outline:\n- Einordnung: Rahmen für: {topic}"
        resp = {"ok": True, "topic": topic, "content": text, "sources": sources}
        with _preview_lock:
            _preview_cache[key] = (now, resp)
        return resp

    @_app.get("/content/preview", tags=["content"])
    def _preview(topic: str = Query(...), k: int = Query(3, ge=1, le=50)):
        return _preview_impl(topic, k)

    @_app.get("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources(topic: str = Query(...), k: int = Query(3, ge=1, le=50)):
        return _preview_impl(topic, k)

    @_app.post("/content/preview", tags=["content"])
    def _preview_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview_impl(topic, k)

    @_app.post("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview_impl(topic, k)

    @_app.post("/content/generate", tags=["content"])
    def _generate(payload: Dict[str, Any] = Body(...)):
        prompt = (payload.get("prompt") or payload.get("topic") or "").strip()
        max_tokens = int(payload.get("max_tokens", 220))
        text = _llm_generate(prompt, max_tokens=max_tokens)
        return {
            "ok": True,
            "text": text,
            "content_map": {"intro": text, "body": "", "outro": "", "bullets": [], "citations": []},
            "sources": []
        }

# install overrides (idempotent)
try:
    _install_preview_overrides(app)
except Exception:
    pass

# ---- OpenAPI operationId de-dup (central, non-invasive) ----
def _install_openapi_operation_id_fix(_app):
    try:
        from fastapi.openapi.utils import get_openapi
    except Exception:
        return
    def custom_openapi():
        if getattr(_app, "openapi_schema", None):
            return _app.openapi_schema
        schema = get_openapi(
            title=getattr(_app, "title", "Stratgen"),
            version=getattr(_app, "version", "0.1.0"),
            description=getattr(_app, "description", None),
            routes=_app.routes,
        )
        seen = set()
        for path, path_item in (schema.get("paths") or {}).items():
            for method, op in list(path_item.items()):
                if method.lower() not in ("get","post","put","patch","delete","options","head"):
                    continue
                base = op.get("operationId") or ""
                new_id = f"{method}_{path}".lower().replace("/","_").replace("{","").replace("}","").replace(".","_").replace("-","_")
                cand = new_id
                i = 1
                while cand in seen:
                    i += 1
                    cand = f"{new_id}_{i}"
                op["operationId"] = cand
                seen.add(cand)
        _app.openapi_schema = schema
        return _app.openapi_schema
    _app.openapi = custom_openapi

try:
    _install_openapi_operation_id_fix(app)
except Exception:
    pass
# --- /quick wins ---

# --- sprint1 quick wins: preview ttl-cache + openapi operationId dedup ---
from fastapi import Query, Body
from fastapi.routing import APIRoute
from typing import List, Dict, Any
import os, requests, pathlib, threading, time

# ---- LLM helper ----
def _llm_generate(prompt: str, max_tokens: int = 220) -> str:
    prov = os.getenv("LLM_PROVIDER", "ollama")
    if prov == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("LLM_MODEL", "mistral")
        try:
            r = requests.post(f"{host}/api/generate",
                              json={"model": model, "prompt": prompt, "stream": False},
                              timeout=60)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception:
            return ""
    return ""

# ---- RAG helpers ----
def _rag_context(q: str, k: int = 5) -> List[Dict[str, Any]]:
    try:
        internal = os.getenv("STRATGEN_INTERNAL_URL", "http://127.0.0.1:8011").rstrip("/")
        r = requests.get(f"{internal}/knowledge/search_semantic",
                         params={"q": q, "k": k}, timeout=30)
        r.raise_for_status()
        hits = r.json().get("_hits") or r.json().get("hits") \
            or r.json().get("results") or r.json().get("items") \
            or r.json().get("sources") or []
        out = []
        for h in hits:
            if isinstance(h, dict):
                path = h.get("path") or h.get("file") or h.get("key")
                score = h.get("score") or h.get("similarity") or 0
                if path:
                    out.append({"path": path, "score": score})
        return out[:k]
    except Exception:
        return []

def _read_snippets(paths: List[Dict[str, Any]], limit_chars: int = 800) -> str:
    out = []
    base = pathlib.Path().resolve()
    for hit in paths:
        p = hit["path"]
        p = pathlib.Path(p)
        if not p.is_absolute():
            p = base / p
        try:
            txt = pathlib.Path(p).read_text(encoding="utf-8", errors="ignore")
            if txt:
                out.append(f"[{hit.get('score',0):.3f}] {txt.strip()[:limit_chars]}")
        except Exception:
            continue
    return "\n\n".join(out)

# ---- TTL cache for preview ----
_PREVIEW_CACHE_TTL = int(os.getenv("PREVIEW_CACHE_TTL", "60"))
_preview_cache: Dict[tuple, tuple] = {}
_preview_lock = threading.Lock()

def _install_preview_overrides(_app):
    # alte preview/generate-Routen entfernen
    targets = {
        ("/content/preview", "GET"), ("/content/preview", "POST"),
        ("/content/preview_with_sources", "GET"), ("/content/preview_with_sources", "POST"),
        ("/content/generate", "POST")
    }
    keep = []
    for r in list(_app.router.routes):
        if isinstance(r, APIRoute) and any((r.path, m) in targets for m in r.methods):
            continue
        keep.append(r)
    _app.router.routes = keep

    def _preview_impl(topic: str, k: int):
        key = (topic, int(k))
        now = time.time()
        with _preview_lock:
            cached = _preview_cache.get(key)
            if cached and (now - cached[0] < _PREVIEW_CACHE_TTL):
                return cached[1]
        sources = _rag_context(topic, k)
        ctx = _read_snippets(sources, 800) if sources else ""
        prompt = f"Write a short, self-contained paragraph about: {topic}."
        if ctx:
            prompt += f"\n\nUse this context where relevant:\n{ctx}"
        text = _llm_generate(prompt) or f"Outline:\n- Einordnung: Rahmen für: {topic}"
        resp = {"ok": True, "topic": topic, "content": text, "sources": sources}
        with _preview_lock:
            _preview_cache[key] = (now, resp)
        return resp

    @_app.get("/content/preview", tags=["content"])
    def _preview(topic: str = Query(...), k: int = Query(3, ge=1, le=50)):
        return _preview_impl(topic, k)

    @_app.get("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources(topic: str = Query(...), k: int = Query(3, ge=1, le=50)):
        return _preview_impl(topic, k)

    @_app.post("/content/preview", tags=["content"])
    def _preview_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview_impl(topic, k)

    @_app.post("/content/preview_with_sources", tags=["content"])
    def _preview_with_sources_post(payload: Dict[str, Any] = Body(...)):
        topic = (payload.get("topic") or payload.get("prompt") or "").strip()
        k = int(payload.get("k", 3))
        return _preview_impl(topic, k)

    @_app.post("/content/generate", tags=["content"])
    def _generate(payload: Dict[str, Any] = Body(...)):
        prompt = (payload.get("prompt") or payload.get("topic") or "").strip()
        max_tokens = int(payload.get("max_tokens", 220))
        text = _llm_generate(prompt, max_tokens=max_tokens)
        return {
            "ok": True,
            "text": text,
            "content_map": {"intro": text, "body": "", "outro": "", "bullets": [], "citations": []},
            "sources": []
        }

try:
    _install_preview_overrides(app)
except Exception:
    pass

# ---- OpenAPI operationId de-dup ----
def _install_openapi_operation_id_fix(_app):
    try:
        from fastapi.openapi.utils import get_openapi
    except Exception:
        return
    def custom_openapi():
        if getattr(_app, "openapi_schema", None):
            return _app.openapi_schema
        schema = get_openapi(
            title=getattr(_app, "title", "Stratgen"),
            version=getattr(_app, "version", "0.1.0"),
            description=getattr(_app, "description", None),
            routes=_app.routes,
        )
        seen = set()
        for path, path_item in (schema.get("paths") or {}).items():
            for method, op in list(path_item.items()):
                if method.lower() not in ("get","post","put","patch","delete","options","head"):
                    continue
                base = op.get("operationId") or ""
                new_id = f"{method}_{path}".lower().replace("/","_").replace("{","").replace("}","").replace(".","_").replace("-","_")
                cand = new_id
                i = 1
                while cand in seen:
                    i += 1
                    cand = f"{new_id}_{i}"
                op["operationId"] = cand
                seen.add(cand)
        _app.openapi_schema = schema
        return _app.openapi_schema
    _app.openapi = custom_openapi

try:
    _install_openapi_operation_id_fix(app)
except Exception:
    pass
# --- /quick wins ---

# --- include agent_run_api (idempotent) ---
try:
    from backend.agent_run_api import router as _agent_run_router
    app.include_router(_agent_run_router)
except Exception as _e:
    # still boot API even if agent router fails
    pass
# --- /include agent_run_api ---

# --- include telemetry_api (idempotent) ---
try:
    from backend.telemetry_api import router as _telemetry_router
    app.include_router(_telemetry_router)
except Exception:
    pass
# --- /include telemetry_api ---

# --- include agent_state_api (idempotent) ---
try:
    from backend.agent_state_api import router as _agent_state_router
    app.include_router(_agent_state_router)
except Exception:
    pass
# --- /include agent_state_api ---

# --- include agent_run_v1_router (idempotent) ---
try:
    from backend.agent_run_v1_router import router as _agent_run_v1_router
    app.include_router(_agent_run_v1_router)
except Exception:
    pass
# --- /include agent_run_v1_router ---
# --- include agent_mission_api (idempotent) ---
try:
    from backend.agent_mission_api import router as _agent_mission_router
    app.include_router(_agent_mission_router)
except Exception:
    pass
# --- /include agent_mission_api ---
# --- include agent_run_v2_router (idempotent) ---
try:
    from backend.agent_run_v2_router import router as _agent_run_v2_router
    app.include_router(_agent_run_v2_router)
except Exception:
    pass
# --- /include agent_run_v2_router ---
# --- include agent_run_alias (idempotent) ---
try:
    from backend.agent_run_alias import router as _agent_run_alias_router
    app.include_router(_agent_run_alias_router)
except Exception:
    pass
# --- /include agent_run_alias ---
try:
    from backend.agent_review_api import router as _agent_review_router
    app.include_router(_agent_review_router)
except Exception:
    pass
try:
    from backend.agent_autotune_api import router as _agent_autotune_router
    app.include_router(_agent_autotune_router)
except Exception:
    pass
