from fastapi import APIRouter, Query, Body
from typing import Optional, List, Dict, Any
import json, urllib.parse, urllib.request, time

from services.textnorm import norm_query

router = APIRouter(prefix="/content", tags=["content"])

def _semantic_sources(topic: str, k: int) -> List[Dict[str, Any]]:
    """Call into our own /knowledge/search_semantic with normalized query."""
    q = norm_query(topic) or topic
    qs = urllib.parse.urlencode({"q": q, "k": int(k)})
    url = f"http://127.0.0.1:8011/knowledge/search_semantic?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("results", [])
    except Exception:
        # Robust fallback
        return []

@router.get("/preview")
def preview(topic: str = Query(...)):
    # Minimal Outline – bleibt wie gehabt
    return {
        "ok": True,
        "topic": topic,
        "outline": [
            {"title": "Einordnung", "bullets": [f"Rahmen für: {topic}"]},
            {"title": "Chancen", "bullets": ["Effizienz", "Skalierung", "Personalisierung"]},
            {"title": "Risiken", "bullets": ["Qualitätssicherung", "Bias", "Datenschutz"]},
        ],
    }

@router.get("/preview_with_sources")
def preview_with_sources(topic: str = Query(...), k: int = Query(5, ge=1, le=50)):
    sources = _semantic_sources(topic, k)
    return {"ok": True, "topic": topic, "k": k, "sources": sources}

@router.post("/generate")
def generate(payload: Dict[str, Any] = Body(...)):
    topic = payload.get("topic", "")
    k = int(payload.get("k", 5))
    section_title = payload.get("section_title", "Überblick")
    customer_name = payload.get("customer_name", "Kunde")
    style = payload.get("style", "b2b_de_sachlich")
    sections = payload.get("sections", [])

    # RAG: hole Quellen analog zu preview_with_sources
    sources = _semantic_sources(topic, k) if topic else []

    # Minimaler Body – strukturiert
    content_map = {
        "intro": f"{section_title}: Kurzüberblick – auf Basis der vorliegenden Hinweise.",
        "body": "Aktuell liegen keine weiteren Details vor.",
        "outro": "Nächster Schritt: Detailtiefe durch weitere interne Dateien erhöhen.",
        "bullets": [],
        "citations": [{"path": s.get("path"), "score": s.get("score")} for s in sources[:k]],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return {
        "ok": True,
        "section_title": section_title,
        "content_map": content_map,
        "sources": sources,
    }


@router.post("/generate")
def generate(body: Dict[str, Any] = Body(...)):
    # Projekt-Kontext holen/konstruieren
    proj = {
        "customer_name": body.get("customer_name") or body.get("org") or "Client",
        "topic": body.get("topic") or "Strategie",
        "meta": {
            "k": int(body.get("k") or 6),
            "slide_plan_len": int(body.get("slides") or body.get("slide_count") or 30),
            "last_modules": body.get("modules") or []
        },
        "facts": body.get("facts") or {},
        "outline": body.get("outline") or {},
        "style": body.get("style") or None,
        "logo": body.get("logo") or None,
    }
    from backend.services.generator import generate_strategy
    res = generate_strategy(proj,
                            slides=proj["meta"]["slide_plan_len"],
                            modules=proj["meta"]["last_modules"])
    return {"ok": True, "meta": {"slide_plan": res["slide_plan"], "content_map": res["content_map"], **res["details"]}}

