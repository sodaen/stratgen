# -*- coding: utf-8 -*-
"""
services/multimodal_export.py
=============================
Stufe 5: Multi-Modal Output

Features:
1. HTML/Reveal.js Export - Interaktive Web-Präsentationen
2. PDF Export - Mit optionalen Speaker Notes
3. Markdown Export - Für Dokumentation
4. JSON Export - Für API-Integration
5. Format Detection - Automatische Format-Wahl

Author: StratGen Agent V3.4
"""
from __future__ import annotations
import os
import re
import json
import base64
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# ============================================
# CONFIGURATION
# ============================================

EXPORTS_DIR = os.getenv("STRATGEN_EXPORTS_DIR", "data/exports")
TEMPLATES_DIR = os.getenv("STRATGEN_TEMPLATES_DIR", "data/templates")
CHARTS_DIR = os.getenv("STRATGEN_CHARTS_DIR", "data/charts")

# Reveal.js CDN
REVEAL_CDN = "https://cdn.jsdelivr.net/npm/reveal.js@4.5.0"

# ============================================
# ENUMS
# ============================================

class ExportFormat(str, Enum):
    PPTX = "pptx"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    JSON = "json"
    REVEAL = "reveal"


# ============================================
# HTML/REVEAL.JS EXPORT
# ============================================

REVEAL_TEMPLATE = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{reveal_cdn}/dist/reset.css">
    <link rel="stylesheet" href="{reveal_cdn}/dist/reveal.css">
    <link rel="stylesheet" href="{reveal_cdn}/dist/theme/{theme}.css">
    <link rel="stylesheet" href="{reveal_cdn}/plugin/highlight/monokai.css">
    <style>
        .reveal h1 {{ font-size: 2.5em; }}
        .reveal h2 {{ font-size: 1.8em; }}
        .reveal ul {{ text-align: left; }}
        .reveal li {{ margin-bottom: 0.5em; }}
        .reveal .slide-number {{ font-size: 0.8em; }}
        .reveal section img {{ max-height: 400px; }}
        .speaker-notes {{ display: none; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 80%; height: auto; }}
        .two-column {{ display: flex; gap: 40px; }}
        .two-column > div {{ flex: 1; }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{slides_html}
        </div>
    </div>
    <script src="{reveal_cdn}/dist/reveal.js"></script>
    <script src="{reveal_cdn}/plugin/notes/notes.js"></script>
    <script src="{reveal_cdn}/plugin/highlight/highlight.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: 'c/t',
            showNotes: false,
            plugins: [ RevealNotes, RevealHighlight ]
        }});
    </script>
</body>
</html>'''


def _slide_to_html(slide: Dict[str, Any], index: int) -> str:
    """Konvertiert einen Slide zu HTML für Reveal.js."""
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    notes = slide.get("notes", "")
    chart = slide.get("chart", "")
    image = slide.get("suggested_image", "")
    
    html_parts = []
    
    # Section öffnen
    html_parts.append(f'            <section data-slide-type="{slide_type}">')
    
    # Titel
    if slide_type == "title":
        html_parts.append(f'                <h1>{_escape_html(title)}</h1>')
        if bullets:
            html_parts.append(f'                <p>{_escape_html(bullets[0])}</p>')
    else:
        html_parts.append(f'                <h2>{_escape_html(title)}</h2>')
    
    # Content Layout
    has_visual = chart or image
    
    if has_visual and bullets:
        # Two-Column Layout
        html_parts.append('                <div class="two-column">')
        html_parts.append('                    <div>')
        
        # Bullets
        if bullets and slide_type != "title":
            html_parts.append('                        <ul>')
            for bullet in bullets[:6]:
                clean_bullet = bullet.strip().lstrip("•-").strip()
                html_parts.append(f'                            <li>{_escape_html(clean_bullet)}</li>')
            html_parts.append('                        </ul>')
        
        html_parts.append('                    </div>')
        html_parts.append('                    <div>')
        
        # Visual
        if chart:
            chart_path = _get_chart_data_uri(chart)
            if chart_path:
                html_parts.append(f'                        <img src="{chart_path}" alt="Chart">')
        elif image:
            image_path = _get_image_data_uri(image)
            if image_path:
                html_parts.append(f'                        <img src="{image_path}" alt="Image">')
        
        html_parts.append('                    </div>')
        html_parts.append('                </div>')
    else:
        # Standard Layout
        if bullets and slide_type != "title":
            html_parts.append('                <ul>')
            for bullet in bullets[:8]:
                clean_bullet = bullet.strip().lstrip("•-").strip()
                html_parts.append(f'                    <li>{_escape_html(clean_bullet)}</li>')
            html_parts.append('                </ul>')
        
        # Chart/Image wenn vorhanden
        if chart:
            chart_path = _get_chart_data_uri(chart)
            if chart_path:
                html_parts.append(f'                <div class="chart-container"><img src="{chart_path}" alt="Chart"></div>')
        elif image:
            image_path = _get_image_data_uri(image)
            if image_path:
                html_parts.append(f'                <div class="chart-container"><img src="{image_path}" alt="Image"></div>')
    
    # Speaker Notes
    if notes:
        html_parts.append(f'                <aside class="notes">{_escape_html(notes)}</aside>')
    
    # Section schließen
    html_parts.append('            </section>')
    
    return '\n'.join(html_parts)


def _escape_html(text: str) -> str:
    """Escaped HTML-Sonderzeichen."""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))


def _get_chart_data_uri(chart_path: str) -> str:
    """Konvertiert Chart zu Data-URI."""
    try:
        full_path = Path(chart_path)
        if not full_path.exists():
            full_path = Path(CHARTS_DIR) / Path(chart_path).name
        
        if full_path.exists():
            with open(full_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = full_path.suffix.lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return f"data:{mime};base64,{data}"
    except Exception:
        pass
    return ""


def _get_image_data_uri(image_path: str) -> str:
    """Konvertiert Bild zu Data-URI."""
    try:
        full_path = Path(image_path)
        if full_path.exists():
            with open(full_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = full_path.suffix.lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            mime = mime_map.get(ext, "image/png")
            return f"data:{mime};base64,{data}"
    except Exception:
        pass
    return ""


def export_to_html(
    slides: List[Dict[str, Any]],
    title: str,
    theme: str = "white",
    include_notes: bool = True
) -> Dict[str, Any]:
    """
    Exportiert Slides als HTML/Reveal.js Präsentation.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        theme: Reveal.js Theme (white, black, league, beige, sky, night, serif, simple, solarized)
        include_notes: Speaker Notes einbinden?
    
    Returns:
        Dictionary mit path, html
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Slides zu HTML konvertieren
    slides_html = []
    for idx, slide in enumerate(slides):
        slide_html = _slide_to_html(slide, idx)
        slides_html.append(slide_html)
    
    # Template füllen
    html = REVEAL_TEMPLATE.format(
        title=_escape_html(title),
        reveal_cdn=REVEAL_CDN,
        theme=theme,
        slides_html='\n'.join(slides_html)
    )
    
    # Speichern
    filename = f"reveal_{_safe_filename(title)}_{int(datetime.now().timestamp())}.html"
    filepath = Path(EXPORTS_DIR) / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return {
        "ok": True,
        "format": "html",
        "path": str(filepath),
        "url": f"/exports/download/{filename}",
        "slides": len(slides),
        "theme": theme
    }


# ============================================
# PDF EXPORT
# ============================================

def export_to_pdf(
    slides: List[Dict[str, Any]],
    title: str,
    include_notes: bool = False,
    slides_per_page: int = 1
) -> Dict[str, Any]:
    """
    Exportiert Slides als PDF.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        include_notes: Speaker Notes als separate Seiten?
        slides_per_page: Slides pro Seite (1, 2, 4, 6)
    
    Returns:
        Dictionary mit path
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Versuche verschiedene PDF-Libraries
    try:
        return _export_pdf_reportlab(slides, title, include_notes, slides_per_page)
    except ImportError:
        pass
    
    try:
        return _export_pdf_fpdf(slides, title, include_notes, slides_per_page)
    except ImportError:
        pass
    
    # Fallback: HTML zu PDF (wenn wkhtmltopdf installiert)
    try:
        return _export_pdf_from_html(slides, title, include_notes)
    except Exception:
        pass
    
    return {"ok": False, "error": "No PDF library available (install reportlab or fpdf2)"}


def _export_pdf_reportlab(
    slides: List[Dict[str, Any]],
    title: str,
    include_notes: bool,
    slides_per_page: int
) -> Dict[str, Any]:
    """PDF-Export mit ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    filename = f"pdf_{_safe_filename(title)}_{int(datetime.now().timestamp())}.pdf"
    filepath = Path(EXPORTS_DIR) / filename
    
    # Landscape A4
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=landscape(A4),
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontSize=28,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=styles['Normal'],
        fontSize=14,
        leftIndent=20,
        spaceBefore=8,
        spaceAfter=8
    )
    notes_style = ParagraphStyle(
        'SlideNotes',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        leftIndent=10
    )
    
    story = []
    
    for idx, slide in enumerate(slides):
        slide_title = slide.get("title", f"Slide {idx + 1}")
        bullets = slide.get("bullets", [])
        notes = slide.get("notes", "")
        chart = slide.get("chart", "")
        
        # Titel
        story.append(Paragraph(slide_title, title_style))
        story.append(Spacer(1, 20))
        
        # Bullets
        for bullet in bullets[:8]:
            clean_bullet = bullet.strip().lstrip("•-").strip()
            story.append(Paragraph(f"• {clean_bullet}", bullet_style))
        
        # Chart
        if chart:
            chart_path = Path(chart)
            if not chart_path.exists():
                chart_path = Path(CHARTS_DIR) / chart_path.name
            if chart_path.exists():
                try:
                    img = Image(str(chart_path), width=400, height=250)
                    story.append(Spacer(1, 20))
                    story.append(img)
                except Exception:
                    pass
        
        # Notes
        if include_notes and notes:
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"<i>Notes: {notes}</i>", notes_style))
        
        # Page Break
        if idx < len(slides) - 1:
            story.append(PageBreak())
    
    doc.build(story)
    
    return {
        "ok": True,
        "format": "pdf",
        "path": str(filepath),
        "url": f"/exports/download/{filename}",
        "slides": len(slides),
        "include_notes": include_notes
    }


def _export_pdf_fpdf(
    slides: List[Dict[str, Any]],
    title: str,
    include_notes: bool,
    slides_per_page: int
) -> Dict[str, Any]:
    """PDF-Export mit FPDF2."""
    from fpdf import FPDF
    
    filename = f"pdf_{_safe_filename(title)}_{int(datetime.now().timestamp())}.pdf"
    filepath = Path(EXPORTS_DIR) / filename
    
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for idx, slide in enumerate(slides):
        pdf.add_page()
        
        slide_title = slide.get("title", f"Slide {idx + 1}")
        bullets = slide.get("bullets", [])
        notes = slide.get("notes", "")
        chart = slide.get("chart", "")
        
        # Titel
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(0, 15, slide_title, ln=True, align='C')
        pdf.ln(10)
        
        # Bullets
        pdf.set_font('Helvetica', '', 12)
        for bullet in bullets[:8]:
            clean_bullet = bullet.strip().lstrip("•-").strip()
            # Encode für PDF
            try:
                clean_bullet = clean_bullet.encode('latin-1', errors='replace').decode('latin-1')
            except:
                clean_bullet = clean_bullet.encode('ascii', errors='replace').decode('ascii')
            pdf.multi_cell(0, 8, f"• {clean_bullet}")
        
        # Chart
        if chart:
            chart_path = Path(chart)
            if not chart_path.exists():
                chart_path = Path(CHARTS_DIR) / chart_path.name
            if chart_path.exists():
                try:
                    pdf.ln(10)
                    pdf.image(str(chart_path), x=80, w=120)
                except Exception:
                    pass
        
        # Notes
        if include_notes and notes:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(128, 128, 128)
            try:
                notes = notes.encode('latin-1', errors='replace').decode('latin-1')
            except:
                notes = notes.encode('ascii', errors='replace').decode('ascii')
            pdf.multi_cell(0, 6, f"Notes: {notes[:300]}")
            pdf.set_text_color(0, 0, 0)
    
    pdf.output(str(filepath))
    
    return {
        "ok": True,
        "format": "pdf",
        "path": str(filepath),
        "url": f"/exports/download/{filename}",
        "slides": len(slides),
        "include_notes": include_notes
    }


def _export_pdf_from_html(
    slides: List[Dict[str, Any]],
    title: str,
    include_notes: bool
) -> Dict[str, Any]:
    """PDF-Export via HTML (benötigt wkhtmltopdf)."""
    import subprocess
    
    # Erst HTML exportieren
    html_result = export_to_html(slides, title, theme="white", include_notes=include_notes)
    if not html_result.get("ok"):
        return html_result
    
    html_path = html_result["path"]
    filename = f"pdf_{_safe_filename(title)}_{int(datetime.now().timestamp())}.pdf"
    pdf_path = Path(EXPORTS_DIR) / filename
    
    # wkhtmltopdf aufrufen
    try:
        result = subprocess.run(
            ["wkhtmltopdf", "--orientation", "Landscape", html_path, str(pdf_path)],
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0 and pdf_path.exists():
            return {
                "ok": True,
                "format": "pdf",
                "path": str(pdf_path),
                "url": f"/exports/download/{filename}",
                "slides": len(slides)
            }
    except Exception:
        pass
    
    return {"ok": False, "error": "wkhtmltopdf failed"}


# ============================================
# MARKDOWN EXPORT
# ============================================

def export_to_markdown(
    slides: List[Dict[str, Any]],
    title: str,
    include_notes: bool = True
) -> Dict[str, Any]:
    """
    Exportiert Slides als Markdown.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        include_notes: Speaker Notes einbinden?
    
    Returns:
        Dictionary mit path, markdown
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Generiert am {datetime.now().strftime('%d.%m.%Y %H:%M')}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for idx, slide in enumerate(slides):
        slide_title = slide.get("title", f"Slide {idx + 1}")
        slide_type = slide.get("type", "content")
        bullets = slide.get("bullets", [])
        notes = slide.get("notes", "")
        
        # Slide Header
        if slide_type == "title":
            lines.append(f"## {slide_title}")
        else:
            lines.append(f"### {idx + 1}. {slide_title}")
        lines.append("")
        
        # Bullets
        for bullet in bullets:
            clean_bullet = bullet.strip().lstrip("•-").strip()
            lines.append(f"- {clean_bullet}")
        
        if bullets:
            lines.append("")
        
        # Notes
        if include_notes and notes:
            lines.append(f"> **Notes:** {notes}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    markdown = '\n'.join(lines)
    
    # Speichern
    filename = f"md_{_safe_filename(title)}_{int(datetime.now().timestamp())}.md"
    filepath = Path(EXPORTS_DIR) / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    return {
        "ok": True,
        "format": "markdown",
        "path": str(filepath),
        "url": f"/exports/download/{filename}",
        "slides": len(slides),
        "markdown": markdown
    }


# ============================================
# JSON EXPORT
# ============================================

def export_to_json(
    slides: List[Dict[str, Any]],
    title: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Exportiert Slides als JSON.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        metadata: Zusätzliche Metadaten
    
    Returns:
        Dictionary mit path, json
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    export_data = {
        "title": title,
        "generated_at": datetime.now().isoformat(),
        "slide_count": len(slides),
        "metadata": metadata or {},
        "slides": slides
    }
    
    # Speichern
    filename = f"json_{_safe_filename(title)}_{int(datetime.now().timestamp())}.json"
    filepath = Path(EXPORTS_DIR) / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return {
        "ok": True,
        "format": "json",
        "path": str(filepath),
        "url": f"/exports/download/{filename}",
        "slides": len(slides)
    }


# ============================================
# MULTI-FORMAT EXPORT
# ============================================

def export_presentation(
    slides: List[Dict[str, Any]],
    title: str,
    formats: List[str] = None,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Exportiert Präsentation in mehrere Formate.
    
    Args:
        slides: Liste der Slides
        title: Präsentationstitel
        formats: Liste der Formate ["pptx", "html", "pdf", "markdown", "json"]
        options: Format-spezifische Optionen
    
    Returns:
        Dictionary mit exports pro Format
    """
    if formats is None:
        formats = ["html", "json"]
    
    options = options or {}
    results = {
        "ok": True,
        "title": title,
        "slide_count": len(slides),
        "exports": {}
    }
    
    for fmt in formats:
        fmt_lower = fmt.lower()
        
        try:
            if fmt_lower == "html" or fmt_lower == "reveal":
                result = export_to_html(
                    slides=slides,
                    title=title,
                    theme=options.get("theme", "white"),
                    include_notes=options.get("include_notes", True)
                )
            elif fmt_lower == "pdf":
                result = export_to_pdf(
                    slides=slides,
                    title=title,
                    include_notes=options.get("include_notes", False),
                    slides_per_page=options.get("slides_per_page", 1)
                )
            elif fmt_lower == "markdown" or fmt_lower == "md":
                result = export_to_markdown(
                    slides=slides,
                    title=title,
                    include_notes=options.get("include_notes", True)
                )
            elif fmt_lower == "json":
                result = export_to_json(
                    slides=slides,
                    title=title,
                    metadata=options.get("metadata")
                )
            else:
                result = {"ok": False, "error": f"Unknown format: {fmt}"}
            
            results["exports"][fmt_lower] = result
            
        except Exception as e:
            results["exports"][fmt_lower] = {"ok": False, "error": str(e)}
    
    return results


# ============================================
# HELPER FUNCTIONS
# ============================================

def _safe_filename(text: str) -> str:
    """Erstellt einen sicheren Dateinamen."""
    # Nur alphanumerische Zeichen und Unterstriche
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe[:50]


def get_available_formats() -> Dict[str, Any]:
    """Gibt verfügbare Export-Formate zurück."""
    formats = {
        "html": {"available": True, "description": "Reveal.js Web-Präsentation"},
        "markdown": {"available": True, "description": "Markdown-Dokument"},
        "json": {"available": True, "description": "JSON-Daten"},
    }
    
    # PDF-Unterstützung prüfen
    try:
        import reportlab
        formats["pdf"] = {"available": True, "library": "reportlab", "description": "PDF-Dokument"}
    except ImportError:
        try:
            import fpdf
            formats["pdf"] = {"available": True, "library": "fpdf", "description": "PDF-Dokument"}
        except ImportError:
            formats["pdf"] = {"available": False, "description": "PDF (install reportlab or fpdf2)"}
    
    return formats


def check_status() -> Dict[str, Any]:
    """Gibt den Status des Export-Systems zurück."""
    return {
        "ok": True,
        "formats": get_available_formats(),
        "exports_dir": EXPORTS_DIR,
        "reveal_cdn": REVEAL_CDN
    }
