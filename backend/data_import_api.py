# -*- coding: utf-8 -*-
"""
StratGen – Data Import API (Sprint 3)
CSV/XLSX Upload → Daten extrahieren → Chart generieren → Slide-Format

Endpoints:
  POST /data-import/upload     – CSV/XLSX hochladen, Daten extrahieren
  POST /data-import/chart      – Aus extrahierten Daten Chart generieren
  POST /data-import/to-slide   – Kompletter Flow: Datei → fertige Slide
  GET  /data-import/list       – Alle importierten Datensätze
  GET  /data-import/{id}       – Einzelnen Datensatz abrufen
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

log = logging.getLogger("stratgen.data_import")

router = APIRouter(prefix="/data-import", tags=["data-import"])

IMPORT_DIR = Path("data/imports")
IMPORT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR = Path("data/exports/charts")
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# PARSE HELPERS
# ─────────────────────────────────────────────

def _parse_csv(content: bytes, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """CSV → Liste von Dicts."""
    try:
        import csv
        text = content.decode(encoding, errors="replace")
        # Trennzeichen erkennen
        sample = text[:2000]
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        reader = csv.DictReader(StringIO(text), dialect=dialect)
        rows = []
        for row in reader:
            # Leere Zeilen überspringen
            if any(v and str(v).strip() for v in row.values()):
                rows.append({k.strip(): v.strip() if v else "" for k, v in row.items()})
        return rows
    except Exception as e:
        log.warning("CSV parse error: %s", e)
        return []


def _parse_xlsx(content: bytes) -> List[Dict[str, Any]]:
    """XLSX → Liste von Dicts (aktives Sheet)."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        # Header in erster Zeile mit Inhalt finden
        header = None
        data_start = 0
        for i, row in enumerate(rows[:10]):
            if any(v is not None and str(v).strip() for v in row):
                header = [str(v).strip() if v is not None else f"col_{j}" for j, v in enumerate(row)]
                data_start = i + 1
                break
        if not header:
            return []
        result = []
        for row in rows[data_start:]:
            if not any(v is not None for v in row):
                continue
            result.append({header[j]: (str(v).strip() if v is not None else "") for j, v in enumerate(row) if j < len(header)})
        return result
    except ImportError:
        log.warning("openpyxl not installed")
        return []
    except Exception as e:
        log.warning("XLSX parse error: %s", e)
        return []


def _infer_columns(rows: List[Dict]) -> Dict[str, Any]:
    """
    Erkennt Label- und Wert-Spalten automatisch.
    Returns: {label_col, value_cols, numeric_cols, text_cols}
    """
    if not rows:
        return {}

    all_cols = list(rows[0].keys())
    numeric_cols = []
    text_cols = []

    for col in all_cols:
        values = [r.get(col, "") for r in rows if r.get(col, "")]
        numeric_count = 0
        for v in values:
            try:
                float(str(v).replace(",", ".").replace("%", "").strip())
                numeric_count += 1
            except Exception:
                pass
        if numeric_count / max(len(values), 1) > 0.7:
            numeric_cols.append(col)
        else:
            text_cols.append(col)

    # Label-Spalte: erste Text-Spalte
    label_col = text_cols[0] if text_cols else all_cols[0]

    return {
        "label_col": label_col,
        "value_cols": numeric_cols,
        "numeric_cols": numeric_cols,
        "text_cols": text_cols,
        "all_cols": all_cols,
    }


def _rows_to_chart_data(
    rows: List[Dict],
    label_col: str,
    value_col: str,
    max_points: int = 20,
) -> Dict[str, Any]:
    """Extrahiert Labels + Values aus Rows für Chart-Generierung."""
    labels = []
    values = []
    for row in rows[:max_points]:
        label = str(row.get(label_col, "")).strip()
        val_raw = str(row.get(value_col, "")).strip()
        val_raw = val_raw.replace(",", ".").replace("%", "").replace("€", "").replace("$", "").strip()
        try:
            val = float(val_raw)
            if label:
                labels.append(label)
                values.append(val)
        except Exception:
            continue
    return {"labels": labels, "values": values}


def _detect_chart_type(value_col: str, labels: List[str]) -> str:
    """Einfache Heuristik für Chart-Typ."""
    col_lower = value_col.lower()
    # Zeit-Indikatoren → Line Chart
    time_words = ["datum", "date", "monat", "month", "quartal", "quarter", "jahr", "year", "woche", "week", "kw"]
    label_sample = " ".join(str(l).lower() for l in labels[:5])
    if any(w in col_lower for w in time_words) or any(w in label_sample for w in time_words):
        return "line"
    # Anteil/Prozent → Pie
    if any(w in col_lower for w in ["anteil", "share", "pct", "prozent", "%"]):
        return "pie"
    # Standard → Bar
    return "bar"


def _generate_chart_png(
    labels: List[str],
    values: List[float],
    chart_type: str,
    title: str,
    unit: str = "",
) -> Optional[Path]:
    """Generiert Chart-PNG mit matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(10, 5.5))
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#F8FAFC")

        # Farben
        colors = ["#1E40AF", "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
                  "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16", "#F97316"]

        if chart_type == "pie":
            ax.pie(values, labels=labels, colors=colors[:len(values)],
                   autopct="%1.1f%%", startangle=140,
                   textprops={"fontsize": 11})
        elif chart_type == "line":
            ax.plot(labels, values, color="#1E40AF", linewidth=2.5,
                    marker="o", markersize=6, markerfacecolor="#10B981")
            ax.fill_between(range(len(labels)), values, alpha=0.08, color="#1E40AF")
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=10)
            ax.grid(axis="y", alpha=0.3)
        else:  # bar
            x = np.arange(len(labels))
            bars = ax.bar(x, values, color=colors[:len(values)], width=0.6,
                          edgecolor="white", linewidth=0.5)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=10)
            ax.grid(axis="y", alpha=0.3)
            # Werte über Balken
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        f"{val:,.1f}{unit}", ha="center", va="bottom", fontsize=9, color="#374151")

        ax.set_title(title, fontsize=14, fontweight="bold", color="#111827", pad=12)
        if unit and chart_type != "pie":
            ax.set_ylabel(unit, fontsize=10, color="#6B7280")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        filename = f"chart-{uuid.uuid4().hex[:8]}.png"
        out_path = CHART_DIR / filename
        plt.tight_layout()
        plt.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor="#FFFFFF")
        plt.close(fig)
        return out_path
    except ImportError:
        log.warning("matplotlib not installed")
        return None
    except Exception as e:
        log.warning("Chart generation failed: %s", e)
        return None


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    label_col: Optional[str] = Form(None),
    value_col: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
):
    """
    CSV oder XLSX hochladen → Daten extrahieren + Spalten erkennen.
    Gibt strukturierte Daten zurück die direkt für Chart-Generierung nutzbar sind.
    """
    content = await file.read()
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()

    # Parsen
    if ext in (".xlsx", ".xls", ".xlsm"):
        rows = _parse_xlsx(content)
    elif ext in (".csv", ".tsv", ".txt"):
        rows = _parse_csv(content)
    else:
        # Versuche CSV als Fallback
        rows = _parse_csv(content)

    if not rows:
        raise HTTPException(400, f"Keine Daten in {filename} gefunden oder Format nicht unterstützt")

    # Spalten inferieren
    col_info = _infer_columns(rows)
    used_label_col = label_col or col_info.get("label_col", "")
    used_value_col = value_col or (col_info.get("value_cols") or [None])[0]

    # Daten persistieren
    import_id = str(uuid.uuid4())
    meta = {
        "id": import_id,
        "filename": filename,
        "customer_name": customer_name,
        "title": title or Path(filename).stem,
        "row_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "col_info": col_info,
        "label_col": used_label_col,
        "value_col": used_value_col,
        "created_at": time.time(),
    }

    # Rohdaten + Meta speichern
    import_file = IMPORT_DIR / f"{import_id}.json"
    import_file.write_text(
        json.dumps({"meta": meta, "rows": rows[:500]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "import_id": import_id,
        "filename": filename,
        "row_count": len(rows),
        "columns": meta["columns"],
        "detected": {
            "label_col": used_label_col,
            "value_col": used_value_col,
            "numeric_cols": col_info.get("numeric_cols", []),
            "text_cols": col_info.get("text_cols", []),
        },
        "preview": rows[:5],
    }


class ChartRequest(BaseModel):
    import_id: str
    label_col: Optional[str] = None
    value_col: Optional[str] = None
    chart_type: Optional[str] = None   # bar|line|pie|auto
    title: Optional[str] = None
    unit: Optional[str] = ""
    max_points: int = 20


@router.post("/chart")
def generate_chart(req: ChartRequest):
    """
    Aus einem importierten Datensatz einen Chart generieren.
    Gibt Slide-Dict zurück das direkt in PPTX-Export genutzt werden kann.
    """
    import_file = IMPORT_DIR / f"{req.import_id}.json"
    if not import_file.exists():
        raise HTTPException(404, f"Import {req.import_id} nicht gefunden")

    data = json.loads(import_file.read_text(encoding="utf-8"))
    meta = data["meta"]
    rows = data["rows"]

    label_col = req.label_col or meta.get("label_col", "")
    value_col = req.value_col or meta.get("value_col", "")
    title = req.title or meta.get("title", "Daten")

    if not label_col or not value_col:
        raise HTTPException(400, "label_col und value_col erforderlich")

    # Daten extrahieren
    chart_data = _rows_to_chart_data(rows, label_col, value_col, req.max_points)
    if not chart_data["labels"]:
        raise HTTPException(400, f"Keine numerischen Werte in Spalte '{value_col}' gefunden")

    # Chart-Typ
    chart_type = req.chart_type
    if not chart_type or chart_type == "auto":
        chart_type = _detect_chart_type(value_col, chart_data["labels"])

    # Chart PNG generieren
    chart_path = _generate_chart_png(
        labels=chart_data["labels"],
        values=chart_data["values"],
        chart_type=chart_type,
        title=title,
        unit=req.unit or "",
    )

    # Slide-Dict bauen (kompatibel mit PPTXDesignerV2)
    bullets = [
        f"{lbl}: {val:,.1f}{req.unit or ''}"
        for lbl, val in zip(chart_data["labels"][:8], chart_data["values"][:8])
    ]

    slide = {
        "type": "chart",
        "title": title,
        "bullets": bullets,
        "chart_type": chart_type,
        "chart_path": str(chart_path) if chart_path else None,
        "image": str(chart_path) if chart_path else None,
        "data": chart_data,
        "source": meta.get("filename", ""),
        "sources": [f"Datenquelle: {meta.get('filename', 'Import')}"],
    }

    # Metadaten updaten
    meta["last_chart"] = {
        "chart_type": chart_type,
        "chart_path": str(chart_path) if chart_path else None,
        "label_col": label_col,
        "value_col": value_col,
        "generated_at": time.time(),
    }
    import_file.write_text(
        json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "chart_type": chart_type,
        "chart_path": str(chart_path) if chart_path else None,
        "chart_url": f"/data-import/chart-image/{chart_path.name}" if chart_path else None,
        "data_points": len(chart_data["labels"]),
        "slide": slide,
    }


@router.post("/to-slide")
async def file_to_slide(
    file: UploadFile = File(...),
    chart_type: Optional[str] = Form("auto"),
    title: Optional[str] = Form(None),
    unit: Optional[str] = Form(""),
    customer_name: Optional[str] = Form(None),
    label_col: Optional[str] = Form(None),
    value_col: Optional[str] = Form(None),
):
    """
    Kompletter Flow: Datei hochladen → Chart generieren → Slide zurückgeben.
    One-Shot für Frontend.
    """
    # Upload
    upload_result = await upload_data_file(file, label_col, value_col, title, customer_name)
    import_id = upload_result["import_id"]

    # Chart
    chart_req = ChartRequest(
        import_id=import_id,
        label_col=label_col or upload_result["detected"]["label_col"],
        value_col=value_col or upload_result["detected"]["value_col"],
        chart_type=chart_type or "auto",
        title=title or upload_result["filename"],
        unit=unit or "",
    )
    chart_result = generate_chart(chart_req)

    return {
        "ok": True,
        "import_id": import_id,
        "filename": upload_result["filename"],
        "row_count": upload_result["row_count"],
        "chart_type": chart_result["chart_type"],
        "chart_url": chart_result.get("chart_url"),
        "slide": chart_result["slide"],
        "detected_columns": upload_result["detected"],
    }


@router.get("/chart-image/{filename}")
def get_chart_image(filename: str):
    """Gibt ein generiertes Chart-Bild zurück."""
    from fastapi.responses import FileResponse
    path = CHART_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Chart nicht gefunden")
    return FileResponse(str(path), media_type="image/png")


@router.get("/list")
def list_imports(customer_name: Optional[str] = Query(None)):
    """Listet alle importierten Datensätze."""
    imports = []
    for f in sorted(IMPORT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))["meta"]
            if customer_name and meta.get("customer_name") != customer_name:
                continue
            imports.append({
                "id": meta["id"],
                "filename": meta["filename"],
                "title": meta.get("title"),
                "customer_name": meta.get("customer_name"),
                "row_count": meta.get("row_count", 0),
                "columns": meta.get("columns", []),
                "created_at": meta.get("created_at", 0),
                "has_chart": "last_chart" in meta,
            })
        except Exception:
            continue
    return {"ok": True, "imports": imports, "count": len(imports)}


@router.get("/{import_id}")
def get_import(import_id: str):
    """Einzelnen Import mit Daten abrufen."""
    f = IMPORT_DIR / f"{import_id}.json"
    if not f.exists():
        raise HTTPException(404, "Import nicht gefunden")
    data = json.loads(f.read_text(encoding="utf-8"))
    return {"ok": True, "meta": data["meta"], "preview": data["rows"][:10]}
