# -*- coding: utf-8 -*-
"""
services/chart_generator.py
===========================
Generiert Charts und Grafiken aus Daten.
Output: PNG-Dateien für Einbettung in PPTX.

Unterstützte Chart-Typen:
- bar: Balkendiagramm
- line: Liniendiagramm
- pie: Tortendiagramm
- timeline: Zeitachse/Roadmap
- comparison: Vergleichsmatrix
- funnel: Trichter-Diagramm
- gauge: Tachonadel (KPI)
"""
from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Matplotlib für Chart-Generierung
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# NumPy für Berechnungen
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# ============================================
# KONFIGURATION
# ============================================

CHARTS_DIR = os.getenv("STRATGEN_CHARTS_DIR", "data/charts")
DEFAULT_DPI = 150
DEFAULT_FIGSIZE = (10, 6)

# Farbpaletten
COLORS = {
    "primary": "#2563EB",      # Blau
    "secondary": "#7C3AED",    # Violett
    "success": "#10B981",      # Grün
    "warning": "#F59E0B",      # Orange
    "danger": "#EF4444",       # Rot
    "neutral": "#6B7280",      # Grau
}

PALETTE = [
    "#2563EB", "#7C3AED", "#10B981", "#F59E0B", 
    "#EF4444", "#EC4899", "#14B8A6", "#8B5CF6"
]

# ============================================
# HELPERS
# ============================================

def _ensure_dir():
    """Stellt sicher dass das Chart-Verzeichnis existiert."""
    os.makedirs(CHARTS_DIR, exist_ok=True)


def _generate_filename(chart_type: str, data_hash: str) -> str:
    """Generiert einen eindeutigen Dateinamen."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{chart_type}_{data_hash[:8]}_{timestamp}.png"


def _data_hash(data: Any) -> str:
    """Berechnet Hash für Cache-Key."""
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def _apply_style(ax, title: str = None, style: Dict[str, Any] = None):
    """Wendet einheitlichen Stil auf Axes an."""
    style = style or {}
    
    # Titel
    if title:
        ax.set_title(title, fontsize=style.get("title_size", 14), fontweight="bold", pad=15)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle="--")
    
    # Spines (Rahmen)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    
    # Font
    ax.tick_params(labelsize=style.get("label_size", 10))


# ============================================
# BAR CHART
# ============================================

def create_bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "",
    ylabel: str = "",
    colors: List[str] = None,
    horizontal: bool = False,
    show_values: bool = True,
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt ein Balkendiagramm.
    
    Args:
        labels: Beschriftungen der Balken
        values: Werte der Balken
        title: Diagrammtitel
        ylabel: Y-Achsen-Beschriftung
        colors: Optionale Farbliste
        horizontal: Horizontale Balken
        show_values: Werte auf Balken anzeigen
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    colors = colors or PALETTE[:len(labels)]
    if len(colors) < len(labels):
        colors = colors * (len(labels) // len(colors) + 1)
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    if horizontal:
        bars = ax.barh(labels, values, color=colors[:len(labels)])
        if ylabel:
            ax.set_xlabel(ylabel)
        if show_values:
            for bar, val in zip(bars, values):
                ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height()/2, 
                       f"{val:,.0f}" if val >= 1 else f"{val:.1%}",
                       va="center", fontsize=9)
    else:
        bars = ax.bar(labels, values, color=colors[:len(labels)])
        if ylabel:
            ax.set_ylabel(ylabel)
        if show_values:
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                       f"{val:,.0f}" if val >= 1 else f"{val:.1%}",
                       ha="center", va="bottom", fontsize=9)
        plt.xticks(rotation=45, ha="right")
    
    _apply_style(ax, title, style)
    plt.tight_layout()
    
    filename = _generate_filename("bar", _data_hash({"labels": labels, "values": values}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "bar"}


# ============================================
# LINE CHART
# ============================================

def create_line_chart(
    x_values: List[Any],
    y_series: Dict[str, List[float]],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    show_markers: bool = True,
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt ein Liniendiagramm.
    
    Args:
        x_values: X-Achsen-Werte
        y_series: Dict mit Serienname -> Werte
        title: Diagrammtitel
        xlabel, ylabel: Achsenbeschriftungen
        show_markers: Datenpunkte markieren
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    for i, (name, values) in enumerate(y_series.items()):
        color = PALETTE[i % len(PALETTE)]
        marker = "o" if show_markers else None
        ax.plot(x_values[:len(values)], values, label=name, color=color, 
               marker=marker, markersize=6, linewidth=2)
    
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if len(y_series) > 1:
        ax.legend(loc="best")
    
    _apply_style(ax, title, style)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    filename = _generate_filename("line", _data_hash({"x": x_values, "y": y_series}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "line"}


# ============================================
# PIE CHART
# ============================================

def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "",
    colors: List[str] = None,
    show_percentages: bool = True,
    explode: List[float] = None,
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt ein Tortendiagramm.
    
    Args:
        labels: Segment-Beschriftungen
        values: Segment-Werte
        title: Diagrammtitel
        colors: Optionale Farbliste
        show_percentages: Prozente anzeigen
        explode: Hervorhebung (z.B. [0.1, 0, 0, 0])
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    colors = colors or PALETTE[:len(labels)]
    fig, ax = plt.subplots(figsize=(8, 8))
    
    autopct = "%1.1f%%" if show_percentages else None
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=labels, 
        colors=colors[:len(labels)],
        autopct=autopct,
        explode=explode,
        startangle=90,
        shadow=False
    )
    
    if show_percentages:
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight("bold")
    
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    
    plt.tight_layout()
    
    filename = _generate_filename("pie", _data_hash({"labels": labels, "values": values}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "pie"}


# ============================================
# TIMELINE / ROADMAP
# ============================================

def create_timeline(
    phases: List[Dict[str, Any]],
    title: str = "Roadmap",
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt eine Roadmap/Timeline.
    
    Args:
        phases: Liste von Dicts mit: name, duration, description, color (optional)
                Beispiel: [{"name": "Phase 1", "duration": "Q1", "description": "Pilot"}]
        title: Diagrammtitel
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    fig, ax = plt.subplots(figsize=(12, 4))
    
    n = len(phases)
    width = 1.0 / n
    
    for i, phase in enumerate(phases):
        color = phase.get("color", PALETTE[i % len(PALETTE)])
        x = i * width
        
        # Phase-Box
        rect = FancyBboxPatch(
            (x + 0.02, 0.3), width - 0.04, 0.4,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="white",
            linewidth=2
        )
        ax.add_patch(rect)
        
        # Phase-Name
        ax.text(x + width/2, 0.5, phase.get("name", f"Phase {i+1}"),
               ha="center", va="center", fontsize=11, fontweight="bold", color="white")
        
        # Duration
        ax.text(x + width/2, 0.15, phase.get("duration", ""),
               ha="center", va="center", fontsize=9, color=COLORS["neutral"])
        
        # Description
        desc = phase.get("description", "")
        if desc:
            ax.text(x + width/2, 0.8, desc[:30] + ("..." if len(desc) > 30 else ""),
                   ha="center", va="center", fontsize=8, color=COLORS["neutral"])
        
        # Pfeil zum nächsten
        if i < n - 1:
            ax.annotate("", xy=(x + width + 0.01, 0.5), xytext=(x + width - 0.01, 0.5),
                       arrowprops=dict(arrowstyle="->", color=COLORS["neutral"], lw=2))
    
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(0, 1)
    ax.axis("off")
    
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
    
    plt.tight_layout()
    
    filename = _generate_filename("timeline", _data_hash(phases))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "timeline"}


# ============================================
# COMPARISON MATRIX
# ============================================

def create_comparison_matrix(
    items: List[str],
    criteria: List[str],
    scores: List[List[float]],
    title: str = "Vergleich",
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt eine Vergleichsmatrix (Heatmap).
    
    Args:
        items: Zu vergleichende Items (Spalten)
        criteria: Vergleichskriterien (Zeilen)
        scores: 2D-Matrix mit Scores (0-10)
        title: Diagrammtitel
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    fig, ax = plt.subplots(figsize=(max(8, len(items) * 1.5), max(4, len(criteria) * 0.8)))
    
    # Heatmap
    if HAS_NUMPY:
        data = np.array(scores)
    else:
        data = scores
    
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=10)
    
    # Labels
    ax.set_xticks(range(len(items)))
    ax.set_yticks(range(len(criteria)))
    ax.set_xticklabels(items, fontsize=10)
    ax.set_yticklabels(criteria, fontsize=10)
    
    # Werte in Zellen
    for i in range(len(criteria)):
        for j in range(len(items)):
            val = scores[i][j] if i < len(scores) and j < len(scores[i]) else 0
            text_color = "white" if val < 4 or val > 7 else "black"
            ax.text(j, i, f"{val:.0f}", ha="center", va="center", 
                   fontsize=11, fontweight="bold", color=text_color)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Score", fontsize=10)
    
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    
    plt.tight_layout()
    
    filename = _generate_filename("comparison", _data_hash({"items": items, "criteria": criteria}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "comparison"}


# ============================================
# FUNNEL CHART
# ============================================

def create_funnel_chart(
    stages: List[str],
    values: List[float],
    title: str = "Funnel",
    show_conversion: bool = True,
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt ein Trichter-Diagramm.
    
    Args:
        stages: Funnel-Stufen (von oben nach unten)
        values: Werte pro Stufe
        title: Diagrammtitel
        show_conversion: Conversion-Rates anzeigen
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    n = len(stages)
    max_val = max(values) if values else 1
    
    for i, (stage, val) in enumerate(zip(stages, values)):
        # Breite proportional zum Wert
        width = 0.4 + 0.5 * (val / max_val)
        height = 0.8 / n
        y = 1 - (i + 1) * height - 0.05
        x = 0.5 - width / 2
        
        color = PALETTE[i % len(PALETTE)]
        
        # Trapez zeichnen (vereinfacht als Rechteck mit abgerundeten Ecken)
        rect = FancyBboxPatch(
            (x, y), width, height * 0.85,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="white",
            linewidth=2
        )
        ax.add_patch(rect)
        
        # Stage-Name und Wert
        ax.text(0.5, y + height * 0.5, f"{stage}\n{val:,.0f}",
               ha="center", va="center", fontsize=11, fontweight="bold", color="white")
        
        # Conversion Rate
        if show_conversion and i > 0 and values[i-1] > 0:
            conv = val / values[i-1] * 100
            ax.text(0.85, y + height * 0.5, f"{conv:.0f}%",
                   ha="center", va="center", fontsize=10, color=COLORS["neutral"])
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
    
    plt.tight_layout()
    
    filename = _generate_filename("funnel", _data_hash({"stages": stages, "values": values}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "funnel"}


# ============================================
# KPI GAUGE
# ============================================

def create_gauge_chart(
    value: float,
    max_value: float = 100,
    title: str = "",
    unit: str = "%",
    thresholds: Tuple[float, float] = (33, 66),
    style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Erstellt ein Tacho-Diagramm (Gauge).
    
    Args:
        value: Aktueller Wert
        max_value: Maximaler Wert
        title: KPI-Name
        unit: Einheit
        thresholds: (rot_bis, gelb_bis) - Rest ist grün
        style: Stil-Optionen
    
    Returns:
        Dict mit: ok, path, filename
    """
    if not HAS_MATPLOTLIB:
        return {"ok": False, "error": "matplotlib not installed"}
    
    _ensure_dir()
    
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw={"projection": "polar"})
    
    # Nur obere Hälfte
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    
    # Hintergrund-Bögen (Rot, Gelb, Grün)
    if HAS_NUMPY:
        theta1 = np.linspace(np.pi, np.pi * (1 - thresholds[0]/100), 30)
        theta2 = np.linspace(np.pi * (1 - thresholds[0]/100), np.pi * (1 - thresholds[1]/100), 30)
        theta3 = np.linspace(np.pi * (1 - thresholds[1]/100), 0, 30)
        
        ax.fill_between(theta1, 0.7, 1, color=COLORS["danger"], alpha=0.7)
        ax.fill_between(theta2, 0.7, 1, color=COLORS["warning"], alpha=0.7)
        ax.fill_between(theta3, 0.7, 1, color=COLORS["success"], alpha=0.7)
    
    # Nadel
    pct = min(value / max_value, 1.0)
    angle = np.pi * (1 - pct) if HAS_NUMPY else 3.14159 * (1 - pct)
    ax.annotate("", xy=(angle, 0.9), xytext=(angle, 0),
               arrowprops=dict(arrowstyle="wedge,tail_width=0.3", color=COLORS["primary"], lw=3))
    
    # Wert in der Mitte
    ax.text(np.pi/2 if HAS_NUMPY else 1.5708, 0.3, f"{value}{unit}", 
           ha="center", va="center", fontsize=20, fontweight="bold")
    
    ax.set_rticks([])
    ax.set_thetagrids([])
    ax.spines["polar"].set_visible(False)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10, y=0.1)
    
    plt.tight_layout()
    
    filename = _generate_filename("gauge", _data_hash({"value": value, "max": max_value}))
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.savefig(filepath, dpi=DEFAULT_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    
    return {"ok": True, "path": filepath, "filename": filename, "type": "gauge"}


# ============================================
# AUTO CHART (basierend auf Daten-Typ)
# ============================================

def auto_create_chart(
    data: Dict[str, Any],
    title: str = "",
    chart_type: str = None
) -> Dict[str, Any]:
    """
    Erstellt automatisch den passenden Chart-Typ basierend auf Daten.
    
    Args:
        data: Daten-Dict mit verschiedenen möglichen Strukturen
        title: Chart-Titel
        chart_type: Optionaler expliziter Typ
    
    Returns:
        Dict mit: ok, path, filename, type
    """
    # Expliziter Typ
    if chart_type:
        if chart_type == "bar" and "labels" in data and "values" in data:
            return create_bar_chart(data["labels"], data["values"], title)
        if chart_type == "line" and "x" in data and "y" in data:
            return create_line_chart(data["x"], data["y"], title)
        if chart_type == "pie" and "labels" in data and "values" in data:
            return create_pie_chart(data["labels"], data["values"], title)
        if chart_type == "timeline" and "phases" in data:
            return create_timeline(data["phases"], title)
        if chart_type == "funnel" and "stages" in data and "values" in data:
            return create_funnel_chart(data["stages"], data["values"], title)
    
    # Auto-Detection
    if "phases" in data:
        return create_timeline(data["phases"], title)
    if "stages" in data and "values" in data:
        return create_funnel_chart(data["stages"], data["values"], title)
    if "items" in data and "criteria" in data and "scores" in data:
        return create_comparison_matrix(data["items"], data["criteria"], data["scores"], title)
    if "x" in data and "y" in data:
        return create_line_chart(data["x"], data["y"], title)
    if "labels" in data and "values" in data:
        # Pie wenn wenige Werte, sonst Bar
        if len(data["labels"]) <= 6:
            return create_pie_chart(data["labels"], data["values"], title)
        return create_bar_chart(data["labels"], data["values"], title)
    
    return {"ok": False, "error": "Could not determine chart type from data"}


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=== Chart Generator Test ===\n")
    
    if not HAS_MATPLOTLIB:
        print("ERROR: matplotlib not installed!")
        print("Install with: pip install matplotlib")
        exit(1)
    
    # Test Bar Chart
    print("--- Bar Chart ---")
    result = create_bar_chart(
        labels=["Q1", "Q2", "Q3", "Q4"],
        values=[120, 180, 150, 220],
        title="Quarterly Revenue",
        ylabel="€ in Tausend"
    )
    print(f"Created: {result.get('path')}")
    
    # Test Pie Chart
    print("\n--- Pie Chart ---")
    result = create_pie_chart(
        labels=["Organic", "Paid", "Referral", "Direct"],
        values=[45, 25, 15, 15],
        title="Traffic Sources"
    )
    print(f"Created: {result.get('path')}")
    
    # Test Timeline
    print("\n--- Timeline ---")
    result = create_timeline(
        phases=[
            {"name": "Discovery", "duration": "2 Wochen", "description": "Analyse & Scope"},
            {"name": "Pilot", "duration": "4 Wochen", "description": "MVP testen"},
            {"name": "Rollout", "duration": "8 Wochen", "description": "Schrittweise Einführung"},
            {"name": "Optimierung", "duration": "Ongoing", "description": "Continuous Improvement"},
        ],
        title="Projekt-Roadmap"
    )
    print(f"Created: {result.get('path')}")
    
    # Test Funnel
    print("\n--- Funnel Chart ---")
    result = create_funnel_chart(
        stages=["Visitors", "Leads", "MQLs", "SQLs", "Customers"],
        values=[10000, 2500, 800, 200, 50],
        title="Sales Funnel"
    )
    print(f"Created: {result.get('path')}")
    
    print("\n✓ All charts created in:", CHARTS_DIR)
