# -*- coding: utf-8 -*-
"""
backend/pptx_templates_api.py
==============================
Custom PPTX Template Management.

Ermöglicht das Hochladen eigener .pptx-Dateien als Basis-Templates
für die Präsentationsgenerierung.

Endpoints:
  GET  /pptx/templates              Alle verfügbaren Templates
  POST /pptx/templates/upload       Neues Template hochladen
  GET  /pptx/templates/{id}         Template-Details + Vorschau
  DELETE /pptx/templates/{id}       Template löschen
  POST /pptx/templates/{id}/preview Thumbnail generieren
  GET  /pptx/templates/active       Aktives Template
  POST /pptx/templates/{id}/activate Template aktivieren
  POST /pptx/templates/deactivate   Zurück zu Standard

Author: StratGen Sprint 8
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse, FileResponse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/pptx/templates", tags=["pptx_templates"])

# ── Konfiguration ─────────────────────────────────────────────────────────────
TEMPLATE_DIR  = Path(os.getenv("PPTX_TEMPLATE_DIR", "data/pptx_templates"))
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE    = TEMPLATE_DIR / "index.json"
ACTIVE_FILE   = TEMPLATE_DIR / ".active"
MAX_SIZE_MB   = int(os.getenv("PPTX_TEMPLATE_MAX_MB", "50"))


# ── Index-Verwaltung ──────────────────────────────────────────────────────────
def _load_index() -> list[dict]:
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_index(templates: list[dict]) -> None:
    INDEX_FILE.write_text(
        json.dumps(templates, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _get_active_id() -> Optional[str]:
    if ACTIVE_FILE.exists():
        return ACTIVE_FILE.read_text().strip() or None
    return None


def _set_active_id(template_id: Optional[str]) -> None:
    if template_id:
        ACTIVE_FILE.write_text(template_id)
    elif ACTIVE_FILE.exists():
        ACTIVE_FILE.unlink()


def _analyze_template(path: Path) -> dict:
    """Analysiert ein PPTX-Template: Slide-Layouts, Farben, Schriften."""
    info = {
        "slide_count": 0,
        "layouts": [],
        "has_master": False,
        "color_hints": [],
        "font_hints": [],
    }
    try:
        from pptx import Presentation
        from pptx.util import Pt
        prs = Presentation(str(path))
        info["slide_count"] = len(prs.slides)

        # Layouts aus Slide-Master
        if prs.slide_masters:
            info["has_master"] = True
            master = prs.slide_masters[0]
            info["layouts"] = [layout.name for layout in master.slide_layouts[:12]]

            # Theme-Farben extrahieren
            try:
                theme_el = master.element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}theme")
                if theme_el is not None:
                    info["color_hints"] = ["theme_colors_available"]
            except Exception:
                pass

    except Exception as e:
        log.warning("Template analysis failed for %s: %s", path, e)
    return info


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_templates():
    """Alle verfügbaren Custom Templates."""
    templates = _load_index()
    active_id = _get_active_id()
    for t in templates:
        t["is_active"] = t["id"] == active_id
    return JSONResponse({"ok": True, "templates": templates, "active_id": active_id})


@router.get("/active")
def get_active_template():
    """Gibt das aktuell aktive Template zurück (oder null wenn Standard)."""
    active_id = _get_active_id()
    if not active_id:
        return JSONResponse({"ok": True, "active": None, "using_default": True})

    templates = _load_index()
    template = next((t for t in templates if t["id"] == active_id), None)
    if not template:
        _set_active_id(None)
        return JSONResponse({"ok": True, "active": None, "using_default": True})

    return JSONResponse({"ok": True, "active": template, "using_default": False})


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Query(default="", description="Anzeigename (optional)")
):
    """
    Lädt ein .pptx-Template hoch.
    Analysiert automatisch Layouts und Farben.
    """
    # Typ prüfen
    filename = file.filename or ""
    if not filename.lower().endswith(".pptx"):
        raise HTTPException(
            status_code=400,
            detail="Nur .pptx-Dateien werden als Templates akzeptiert."
        )

    # Datei lesen
    content = await file.read()

    # Größe prüfen
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß: {size_mb:.1f} MB (max. {MAX_SIZE_MB} MB)"
        )

    # Hash für Deduplizierung
    file_hash = hashlib.sha256(content).hexdigest()[:16]

    # Prüfen ob bereits vorhanden
    templates = _load_index()
    if any(t.get("hash") == file_hash for t in templates):
        existing = next(t for t in templates if t.get("hash") == file_hash)
        return JSONResponse({
            "ok": True,
            "id": existing["id"],
            "duplicate": True,
            "message": f"Template '{existing['name']}' bereits vorhanden."
        })

    # Template-ID + Pfad
    template_id = str(uuid.uuid4())
    safe_name = f"{template_id}.pptx"
    dest = TEMPLATE_DIR / safe_name
    dest.write_bytes(content)

    # Analysieren
    analysis = _analyze_template(dest)

    # Display-Name
    display_name = name.strip() or filename.replace(".pptx", "").replace("_", " ").replace("-", " ")

    # Index-Eintrag
    entry = {
        "id": template_id,
        "name": display_name,
        "filename": safe_name,
        "original_name": filename,
        "size_kb": round(len(content) / 1024, 1),
        "hash": file_hash,
        "uploaded_at": int(time.time()),
        "slide_count": analysis["slide_count"],
        "layouts": analysis["layouts"][:6],
        "has_master": analysis["has_master"],
    }
    templates.append(entry)
    _save_index(templates)

    log.info("Template uploaded: %s (%s)", display_name, template_id)

    return JSONResponse({
        "ok": True,
        "id": template_id,
        "name": display_name,
        "size_kb": entry["size_kb"],
        "slide_count": analysis["slide_count"],
        "layouts": analysis["layouts"],
        "has_master": analysis["has_master"],
    })


@router.get("/{template_id}")
def get_template(template_id: str):
    """Details eines Templates."""
    templates = _load_index()
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} nicht gefunden")
    template["is_active"] = template["id"] == _get_active_id()
    return JSONResponse({"ok": True, **template})


@router.delete("/{template_id}")
def delete_template(template_id: str):
    """Löscht ein Template. Deaktiviert es falls aktiv."""
    templates = _load_index()
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} nicht gefunden")

    # Datei löschen
    dest = TEMPLATE_DIR / template["filename"]
    if dest.exists():
        dest.unlink()

    # Index aktualisieren
    templates = [t for t in templates if t["id"] != template_id]
    _save_index(templates)

    # Deaktivieren falls aktiv
    if _get_active_id() == template_id:
        _set_active_id(None)

    return JSONResponse({"ok": True, "deleted": template_id})


@router.post("/{template_id}/activate")
def activate_template(template_id: str):
    """Aktiviert ein Template als Standard für neue Präsentationen."""
    templates = _load_index()
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} nicht gefunden")

    _set_active_id(template_id)
    log.info("Template activated: %s (%s)", template["name"], template_id)

    return JSONResponse({
        "ok": True,
        "active_id": template_id,
        "name": template["name"],
        "message": f"Template '{template['name']}' ist jetzt aktiv."
    })


@router.post("/deactivate")
def deactivate_template():
    """Deaktiviert Custom Template → zurück zu StratGen Standard."""
    _set_active_id(None)
    return JSONResponse({"ok": True, "message": "Standard-Template aktiv."})


@router.get("/{template_id}/download")
def download_template(template_id: str):
    """Lädt das Template-File herunter."""
    templates = _load_index()
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} nicht gefunden")

    dest = TEMPLATE_DIR / template["filename"]
    if not dest.exists():
        raise HTTPException(status_code=404, detail="Template-Datei nicht gefunden")

    return FileResponse(
        str(dest),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=template["original_name"]
    )


# ── Hilfsfunktion für Generator ──────────────────────────────────────────────

def get_active_template_path() -> Optional[Path]:
    """
    Gibt den Pfad zum aktiven Template zurück.
    Wird von pptx_designer_v2.py verwendet.

    Returns:
        Path zum .pptx-File oder None wenn Standard-Template
    """
    active_id = _get_active_id()
    if not active_id:
        return None

    templates = _load_index()
    template = next((t for t in templates if t["id"] == active_id), None)
    if not template:
        return None

    dest = TEMPLATE_DIR / template["filename"]
    return dest if dest.exists() else None
