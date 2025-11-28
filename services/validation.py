# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union

from services.compat import ensure_outline_dict, resolve_style

def validate_outline(data: Union[str, Dict[str, Any], None]) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
    """Normalisiert Outline zu Dict und gibt (ok, outline, errors[]) zurück."""
    errors: List[Dict[str, Any]] = []
    outline = ensure_outline_dict(data)

    title = outline.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append({"field": "outline.title", "msg": "Titel fehlt oder ist leer."})

    sections = outline.get("sections")
    if sections is None:
        outline["sections"] = []
        sections = outline["sections"]
    if not isinstance(sections, list):
        errors.append({"field": "outline.sections", "msg": "sections muss eine Liste sein."})
    else:
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                errors.append({"field": f"outline.sections[{i}]", "msg": "Section muss ein Objekt sein."})
                continue
            if not isinstance(sec.get("title"), str) or not sec.get("title", "").strip():
                errors.append({"field": f"outline.sections[{i}].title", "msg": "Section-Titel fehlt oder ist leer."})
            bullets = sec.get("bullets")
            if bullets is not None and not isinstance(bullets, list):
                errors.append({"field": f"outline.sections[{i}].bullets", "msg": "bullets muss eine Liste sein."})

    return (len(errors) == 0), outline, errors

def validate_style(style_like: Union[str, Dict[str, Any], None]) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
    """Liefert (ok, style_options, errors[]). ok=false wenn kein Style auflösbar ist."""
    style = resolve_style(style_like)
    if isinstance(style, dict) and style:
        return True, style, []
    return False, {}, [{"field": "style", "msg": "Unbekannter oder leerer Style."}]

def validate_preview_size(width: Any, height: Any) -> Tuple[bool, List[Dict[str, Any]]]:
    """Einfacher Check für Preview-Bildgrößen."""
    errs: List[Dict[str, Any]] = []
    try:
        w = int(width)
        h = int(height)
    except Exception:
        return False, [{"field": "width/height", "msg": "width/height müssen Integer sein."}]
    if w <= 0 or h <= 0:
        errs.append({"field": "width/height", "msg": "width/height müssen > 0 sein."})
    if w > 4000 or h > 4000:
        errs.append({"field": "width/height", "msg": "width/height zu groß (max 4000)."})
    return (len(errs) == 0), errs
