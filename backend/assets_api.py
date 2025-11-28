from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
import traceback

router = APIRouter(prefix="/assets", tags=["assets"])

def _get_project(project_id:str)->Dict[str,Any]:
    from backend.projects_api import _db_get_project  # reuse
    proj = _db_get_project(project_id)
    if not proj: raise HTTPException(404, "project not found")
    return proj

@router.get("/preview/{project_id}")
def preview_assets(project_id:str):
    try:
        proj = _get_project(project_id)
        plan = (proj.get("meta") or {}).get("slide_plan") or []
        from services.asset_resolver import enrich_plan_with_assets
        enriched = enrich_plan_with_assets(proj, plan) or plan
        # Diff: pro Slide neu hinzugekommene Tokens extrahieren
        def tokens(txt):
            from re import findall
            if not isinstance(txt, str): return []
            return findall(r"#(?:IMG|CHART|TABLE)\([^)]*\)", txt)
        diffs=[]
        for i,(a,b) in enumerate(zip(plan, enriched)):
            before = (tokens((a or {}).get("notes")) + tokens(" ".join((a or {}).get("bullets") or [])))
            after  = (tokens((b or {}).get("notes")) + tokens(" ".join((b or {}).get("bullets") or [])))
            added  = [t for t in after if t not in before]
            if added:
                diffs.append({"index":i, "title": b.get("title"), "added": added})
        return {"ok": True, "count": len(diffs), "diffs": diffs}
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(500, "resolver error")

def _list_uploads(base: str = "data/raw/uploads", limit: int = 50) -> list[str]:
    try:
        files = glob.glob(os.path.join(base, "*"))
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        return files[:limit]
    except Exception:
        return []

@router.get("/assets/preview/{project_id}")
def assets_preview(project_id: str) -> Dict[str, Any]:
    # Projekt laden (bestehenden Getter wiederverwenden)
    try:
        from backend.projects_api import _db_get_project
    except Exception as e:
        raise HTTPException(500, f"projects_api import failed: {e}")

    proj = _db_get_project(project_id)
    if not proj:
        raise HTTPException(404, "project not found")

    meta = (proj.get("meta") or {})
    slide_plan = list(meta.get("slide_plan") or [])
    uploads = _list_uploads()
    logo = proj.get("logo")

    # Kleine, nützliche Preview + Diff-Hinweise
    payload = {
        "ok": True,
        "project_id": project_id,
        "meta": {
            "slide_plan_len": len(slide_plan),
            "last_enrich": meta.get("last_enrich"),
        },
        "assets": {
            "logo": logo,
            "uploads": uploads,
        },
        "diff": {
            "needs_logo": logo is None,
            "uploads_available": len(uploads),
        },
    }
    return payload
