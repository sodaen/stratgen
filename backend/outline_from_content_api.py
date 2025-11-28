from __future__ import annotations


from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

router = APIRouter(prefix="/outline", tags=["outline"])

# ------------------------------- Modelle ------------------------------------

class OutlineFromContentReq(BaseModel):
    customer_name: str
    topic: str
    content_map: Dict[str, Any] = Field(default_factory=dict)
    subtitle: Optional[str] = None
    style: Optional[str] = None  # nur durchreichen (Export nutzt es)

class OutlineResp(BaseModel):
    ok: bool
    outline: Dict[str, Any]

# ------------------------------- Helpers ------------------------------------

def _title_from_key(key: str) -> str:
    t = (key or "").strip().replace("_", " ")
    return t[:1].upper() + t[1:] if t else "Abschnitt"

def _as_bullets(value: Any) -> List[str]:
    # akzeptiert: list[str], list[{text:..}], {bullets:[...]} oder str
    if isinstance(value, dict):
        if "bullets" in value and isinstance(value["bullets"], list):
            return [str(x) for x in value["bullets"]]
        if "items" in value and isinstance(value["items"], list):
            return [str(x.get("text", x)) for x in value["items"]]
    if isinstance(value, list):
        out: List[str] = []
        for x in value:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict) and "text" in x:
                out.append(str(x["text"]))
            else:
                out.append(str(x))
        return out
    if isinstance(value, str):
        return [value]
    return []

def _detect_section(key: str, value: Any) -> Dict[str, Any]:
    """
    Heuristik je Abschnitt:
      - KPI/Beweis: 'big_number' oder 'kpi'
      - Quote: 'quote'
      - 2 Spalten: 'cols.left/right' oder 'left_bullets'/'right_bullets'
      - Bullets: 'bullets' oder Listen/String
    """
    title = _title_from_key(key)
    if isinstance(value, dict):
        # KPI/Beweis
        big = value.get("big_number") or value.get("kpi")
        if big is not None:
            return {
                "title": title,
                "big_number": str(big),
                "label": value.get("label") or "",
                "source": value.get("source") or "",
            }
        # Quote
        if "quote" in value:
            return {
                "title": title,
                "quote": str(value.get("quote") or ""),
                "author": value.get("author") or "",
                "source": value.get("source") or "",
            }
        # Zwei Spalten
        cols = value.get("cols") or {}
        left  = cols.get("left")  if isinstance(cols, dict) else None
        right = cols.get("right") if isinstance(cols, dict) else None
        left_b  = value.get("left_bullets")
        right_b = value.get("right_bullets")
        if left or right or left_b or right_b:
            return {
                "title": title,
                "cols": {
                    "left":  _as_bullets(left if left is not None else left_b or []),
                    "right": _as_bullets(right if right is not None else right_b or []),
                },
            }
        # Bullets (dict mit bullets/items)
        bullets = _as_bullets(value)
        if bullets:
            return {"title": title, "bullets": bullets}
    # Generische Bullets (list/str)
    bullets = _as_bullets(value)
    if bullets:
        return {"title": title, "bullets": bullets}
    # Fallback: leerer Abschnitt
    return {"title": title, "bullets": []}

# ------------------------------- Route --------------------------------------

@router.post("/from-content", response_model=OutlineResp)
def from_content(req: OutlineFromContentReq = Body(...)) -> OutlineResp:
    cm = dict(req.content_map or {})
    skip_keys = {"intro", "summary", "subtitle", "title", "meta"}
    sections: List[Dict[str, Any]] = []
    # intro zuerst, wenn vorhanden
    if "intro" in cm:
        sections.append(_detect_section("Intro", cm["intro"]))
    for k, v in cm.items():
        if k in skip_keys:
            continue
        sections.append(_detect_section(k, v))
    outline: Dict[str, Any] = {
        "subtitle": req.subtitle or cm.get("subtitle") or "",
        "sections": sections,
    }
    return OutlineResp(ok=True, outline=outline)
