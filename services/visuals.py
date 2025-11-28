from __future__ import annotations
import re, uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EXPORT_DIR = Path("data/exports/visuals")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DATA_LINE = re.compile(r"^\s*(?:•\s*)?([^:|]+?)\s*[:|]\s*([0-9][0-9.,%]*)\s*$", re.U | re.I)
CHART_TOKEN = re.compile(r"#CHART(?:\s+type\s*=\s*(bar|line|pie))?", re.I)
TABLE_TOKEN = re.compile(r"#TABLE\b", re.I)

def _safe_path(prefix: str) -> str:
    name = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    return str(EXPORT_DIR / name)

def parse_visual_placeholders(bullets: List[str]) -> Dict[str, Any]:
    """
    Ermittelt aus Bullets:
      - wants_table (bool) / wants_chart (bool, type)
      - Datenpunkte aus "Label: Wert" Zeilen
      - bullets_clean (ohne Tokens + ohne Datenzeilen)
    """
    wants_table = False
    chart_type: Optional[str] = None
    data: List[Tuple[str, float]] = []
    clean: List[str] = []

    for b in bullets:
        b_raw = b.strip()
        if TABLE_TOKEN.search(b_raw):
            wants_table = True
            continue
        m_chart = CHART_TOKEN.search(b_raw)
        if m_chart:
            chart_type = (m_chart.group(1) or "bar").lower()
            continue
        # Datenzeilen
        m = DATA_LINE.match(b_raw)
        if m:
            label = m.group(1).strip()
            val_s = m.group(2).strip().replace("%","").replace(".","").replace(",",".")
            try:
                val = float(val_s)
            except Exception:
                continue
            data.append((label, val))
        else:
            clean.append(b)

    # Heuristik: wenn Chart verlangt, aber kein Typ → bar
    if chart_type is None and any("#CHART" in b.upper() for b in bullets):
        chart_type = "bar"

    return {
        "bullets_clean": clean,
        "wants_table": wants_table,
        "chart_type": chart_type,
        "data": data[:12]  # max 12 Punkte
    }

# ---------- RENDERER ----------

def render_table_png(rows: List[Tuple[str, float]] | List[Tuple[str, str]], title: str = "") -> str:
    if not rows:
        rows = [("TODO", 0.0)]
    df = pd.DataFrame(rows, columns=["Kategorie","Wert"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.2)
    if title:
        ax.set_title(title, pad=10)
    out = _safe_path("table")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out

def render_chart_png(chart_type: str, rows: List[Tuple[str, float]], title: str = "") -> str:
    if not rows:
        # Placeholder-Bild
        return render_table_png([("TODO", 0.0)], title or "CHART TODO")
    labels = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7, 4))
    if chart_type == "pie":
        if sum(values) == 0:
            values = [1 for _ in values]
        ax.pie(values, labels=labels, autopct="%1.0f%%")
        ax.axis("equal")
    elif chart_type == "line":
        ax.plot(x, values, marker="o")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha="right")
    else:
        ax.bar(x, values)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha="right")

    if title:
        ax.set_title(title)
    ax.grid(True, axis="y", linewidth=0.5, alpha=0.4)

    out = _safe_path(chart_type)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def _mpl_ready():
    try:
        import matplotlib  # type: ignore
        return True
    except Exception:
        return False
