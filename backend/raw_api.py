from __future__ import annotations


import json
import time
from pathlib import Path
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.auth import require_api_key

router = APIRouter(
    prefix="/raw",
    tags=["raw"],
    dependencies=[Depends(require_api_key)],
)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

EXTRACTED_DIR = Path("data/raw-extracted")
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


class RawRegisterIn(BaseModel):
    filename: str
    source: Optional[str] = None   # z.B. "agentur", "kunde", "intern"
    tags: Optional[List[str]] = None
    note: Optional[str] = None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/list")
def raw_list():
    items = []
    for p in sorted(RAW_DIR.glob("*.json")):
        data = _load_json(p)
        items.append({
            "name": p.name,
            "filename": data.get("filename"),
            "source": data.get("source"),
            "tags": data.get("tags") or [],
            "created_at": data.get("created_at"),
            "extracted": (EXTRACTED_DIR / p.name).exists(),
        })
    items.sort(key=lambda x: x["created_at"] or 0, reverse=True)
    return {"ok": True, "count": len(items), "items": items}


@router.post("/register")
def raw_register(body: RawRegisterIn):
    ts = int(time.time())
    name = f"raw-{ts}.json"
    doc = {
        "name": name,
        "filename": body.filename,
        "source": body.source,
        "tags": body.tags or [],
        "note": body.note,
        "created_at": ts,
    }
    (RAW_DIR / name).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"ok": True, "name": name, "data": doc}


@router.post("/{name}/extract")
def raw_extract(name: str):
    raw_path = RAW_DIR / name
    if not raw_path.exists():
        raise HTTPException(status_code=404, detail="raw not found")

    raw_doc = _load_json(raw_path)
    filename = raw_doc.get("filename")

    # 1) wenn wir eine echte PPTX-Datei finden, extrahieren wir sie
    if filename and filename.lower().endswith(".pptx"):
        from services import pptx_extract
        real_file = _find_raw_file(filename)
        if real_file is None:
            # wir loggen trotzdem ein Extrakt, aber sagen, dass die Datei fehlt
            extracted = {
                "name": raw_doc["name"],
                "from_filename": filename,
                "created_at": time.time(),
                "pattern": "agency-pitch",
                "error": f"pptx file not found on disk: {filename}",
                "slides": [],
                "tags": raw_doc.get("tags") or [],
                "source": raw_doc.get("source"),
            }
        else:
            pptx_data = pptx_extract.extract_pptx_text(str(real_file))

            # abgeleitete TXT für knowledge
            derived_dir = EXTRACTED_DIR  # wir nutzen den gleichen Ordner
            derived_dir.mkdir(parents=True, exist_ok=True)
            txt_target = Path("data/knowledge/derived") / f"{filename}.txt"
            txt_target.parent.mkdir(parents=True, exist_ok=True)
            pptx_extract.write_flat_txt_from_extract(pptx_data, txt_target)

            extracted = {
                "name": raw_doc["name"],
                "from_filename": filename,
                "created_at": time.time(),
                "pattern": "pptx-agency",
                "slides": pptx_data.get("slides", []),
                "tags": raw_doc.get("tags") or [],
                "source": raw_doc.get("source"),
                "knowledge_txt": str(txt_target),
            }
    else:
        # 2) Fallback auf deinen bisherigen Stub
        extracted = {
            "name": raw_doc["name"],
            "from_filename": raw_doc.get("filename"),
            "created_at": time.time(),
            "pattern": "agency-pitch",
            "slides": [
                {"role": "title", "title": "Titel / Kundenname / Datum"},
                {"role": "agenda", "title": "Agenda"},
                {"role": "section", "title": "Ausgangslage / Problem"},
                {"role": "section", "title": "Lösung / Ansatz"},
                {"role": "section", "title": "Roadmap / Umsetzung"},
                {"role": "closing", "title": "Nächste Schritte"},
            ],
            "tags": raw_doc.get("tags") or [],
            "source": raw_doc.get("source"),
        }

    (EXTRACTED_DIR / name).write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"ok": True, "name": name, "extracted": extracted}

    raw_path = RAW_DIR / name
    if not raw_path.exists():
        raise HTTPException(status_code=404, detail="raw not found")

    raw_doc = _load_json(raw_path)

    # 🔴 Hier ist aktuell nur ein STUB.
    # Später: python-pptx öffnen, Folien-Typen erkennen, Kapitel identifizieren.
    extracted = {
        "name": raw_doc["name"],
        "from_filename": raw_doc["filename"],
        "created_at": time.time(),
        "pattern": "agency-pitch",
        "slides": [
            {"role": "title", "title": "Titel / Kundenname / Datum"},
            {"role": "agenda", "title": "Agenda"},
            {"role": "section", "title": "Ausgangslage / Problem"},
            {"role": "section", "title": "Lösung / Ansatz"},
            {"role": "section", "title": "Roadmap / Umsetzung"},
            {"role": "closing", "title": "Nächste Schritte"},
        ],
        "tags": raw_doc.get("tags") or [],
        "source": raw_doc.get("source"),
    }

    (EXTRACTED_DIR / name).write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"ok": True, "name": name, "extracted": extracted}


@router.get("/extracted")
def raw_extracted_list():
    items = []
    for p in sorted(EXTRACTED_DIR.glob("raw-*.json")):
        data = _load_json(p)
        items.append({
            "name": data.get("name"),
            "pattern": data.get("pattern"),
            "slides": len(data.get("slides") or []),
            "source": data.get("source"),
            "tags": data.get("tags") or [],
            "created_at": data.get("created_at"),
        })
    items.sort(key=lambda x: x["created_at"] or 0, reverse=True)
    return {"ok": True, "count": len(items), "items": items}


# --- Helper: echte Datei zum RAW-Datensatz finden ---
def _find_raw_file(filename: str) -> Path | None:
    candidates = [
        Path("data/raw/uploads") / filename,
        Path("data/raw") / filename,
        Path("data/knowledge/uploads") / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None
