# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional, Dict, List, Tuple
from fastapi import APIRouter
from pydantic import BaseModel

# Wir nutzen die bestehenden Validatoren; falls sie fehlen, gibt's einen defensiven Fallback
try:
    from services.validation import validate_outline, validate_style, validate_preview_size
except Exception:
    from services.compat import ensure_outline_dict, resolve_style
    def validate_outline(data) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
        out = ensure_outline_dict(data)
        errs = []
        if not out.get("title"):
            errs.append({"field":"title","msg":"missing"})
        return (len(errs)==0), out, errs
    def validate_style(style_like) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
        s = resolve_style(style_like)
        ok = bool(s)
        return ok, s, ([] if ok else [{"field":"style","msg":"unknown"}])
    def validate_preview_size(w: Optional[int], h: Optional[int]):
        errs = []
        w2 = int(w) if isinstance(w, int) else 800
        h2 = int(h) if isinstance(h, int) else 450
        if w is not None and w2 <= 0: errs.append({"field":"width","msg":"must be > 0"})
        if h is not None and h2 <= 0: errs.append({"field":"height","msg":"must be > 0"})
        return (len(errs)==0), {"width": w2, "height": h2}, errs

router = APIRouter(prefix="/projects", tags=["projects"])

class ValidateRequest(BaseModel):
    outline: Optional[Any] = None
    style: Optional[Any] = None
    width: Optional[int] = None
    height: Optional[int] = None

@router.post("/validate")
def validate(req: ValidateRequest):
    ok_o, o_val, o_err = validate_outline(req.outline)
    ok_s, s_val, s_err = validate_style(req.style)
    ok_z, z_val, z_err = validate_preview_size(req.width, req.height)
    ok = ok_o and ok_s and ok_z
    return {
        "ok": ok,
        "outline": {"ok": ok_o, "value": o_val, "errors": o_err},
        "style":   {"ok": ok_s, "value": s_val, "errors": s_err},
        "size":    {"ok": ok_z, "value": z_val, "errors": z_err},
    }
