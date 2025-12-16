"""
PPTX Designer V3 - Intelligente Präsentations-Engine für Stratgen.

Features:
- Verschiedene Slide-Typen (chapter, bullets, text, persona, comparison, chart, timeline)
- Kapitel-Struktur mit Hero-Bildern
- Kontextsensitive Content-Darstellung
- Automatische Layout-Auswahl basierend auf Content
- Professionelles Corporate Design

Author: Stratgen Team
Version: 3.0
"""

import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

logger = logging.getLogger(__name__)


class PPTXDesignerV3:
    """
    Intelligente PPTX-Präsentations-Engine.
    
    Erstellt professionelle Präsentationen mit verschiedenen Slide-Typen
    und automatischer Layout-Auswahl basierend auf Content-Komplexität.
    """
    
    # Standard-Farbpaletten
    PALETTES = {
        "corporate": {
            "primary": "#1E40AF",      # Dunkelblau
            "secondary": "#3B82F6",    # Hellblau
            "accent": "#10B981",       # Grün
            "background": "#FFFFFF",   # Weiß
            "text": "#111827",         # Fast Schwarz
            "text_light": "#6B7280",   # Grau
            "chapter_bg": "#1E3A5F",   # Dunkelblau für Kapitel
        },
        "modern": {
            "primary": "#7C3AED",      # Violett
            "secondary": "#A78BFA",    # Hell-Violett
            "accent": "#F59E0B",       # Orange
            "background": "#FFFFFF",
            "text": "#1F2937",
            "text_light": "#9CA3AF",
            "chapter_bg": "#4C1D95",
        },
        "minimal": {
            "primary": "#000000",      # Schwarz
            "secondary": "#4B5563",    # Grau
            "accent": "#DC2626",       # Rot
            "background": "#FFFFFF",
            "text": "#111827",
            "text_light": "#9CA3AF",
            "chapter_bg": "#1F2937",
        }
    }
    
    # Slide-Typ zu Render-Methode Mapping
    SLIDE_RENDERERS = {
        "title": "_render_title_slide",
        "chapter": "_render_chapter_slide",
        "executive_summary": "_render_executive_summary",
        "bullets": "_render_bullets_slide",
        "text": "_render_text_slide",
        "persona": "_render_persona_slide",
        "comparison": "_render_comparison_slide",
        "chart": "_render_chart_slide",
        "timeline": "_render_timeline_slide",
        "quote": "_render_quote_slide",
        "conclusion": "_render_conclusion_slide",
        "contact": "_render_contact_slide",
        # Fallbacks für alte Typen
        "problem": "_render_bullets_slide",
        "solution": "_render_bullets_slide",
        "benefits": "_render_bullets_slide",
        "features": "_render_bullets_slide",
        "approach": "_render_bullets_slide",
        "methodology": "_render_bullets_slide",
        "risks": "_render_bullets_slide",
        "mitigation": "_render_bullets_slide",
        "resources": "_render_bullets_slide",
        "budget": "_render_bullets_slide",
        "roi": "_render_bullets_slide",
        "metrics": "_render_bullets_slide",
        "implementation": "_render_bullets_slide",
        "support": "_render_bullets_slide",
        "faq": "_render_bullets_slide",
        "deep_dive": "_render_text_slide",
        "technical": "_render_text_slide",
        "analysis": "_render_text_slide",
        "context": "_render_text_slide",
        "opportunity": "_render_bullets_slide",
        "data": "_render_bullets_slide",
        "case_study": "_render_text_slide",
        "testimonial": "_render_quote_slide",
        "team": "_render_bullets_slide",
        "process": "_render_bullets_slide",
        "milestones": "_render_timeline_slide",
        "roadmap": "_render_timeline_slide",
        "integration": "_render_bullets_slide",
        "security": "_render_bullets_slide",
        "next_steps": "_render_conclusion_slide",
    }
    
    def __init__(
        self,
        colors: Dict[str, str] = None,
        palette: str = "corporate",
        company_name: str = "",
        include_slide_numbers: bool = True
    ):
        """
        Initialisiert den Designer.
        
        Args:
            colors: Custom Farbdefinitionen
            palette: Farbpalette (corporate, modern, minimal)
            company_name: Firmenname für Footer
            include_slide_numbers: Seitenzahlen anzeigen
        """
        self.palette = self.PALETTES.get(palette, self.PALETTES["corporate"])
        if colors:
            self.palette.update(colors)
        
        self.company_name = company_name
        self.include_slide_numbers = include_slide_numbers
        
        # Präsentation erstellen (16:9)
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        
        self.total_slides = 0
        self.current_chapter = ""
    
    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Konvertiert Hex-Farbe zu RGBColor."""
        hex_color = hex_color.lstrip('#')
        return RGBColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    def _add_background(self, slide, color: str = None, gradient: bool = False):
        """Fügt Hintergrund zu Slide hinzu."""
        if color is None:
            color = self.palette["background"]
        
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = self._hex_to_rgb(color)
    
    def _add_shape(
        self,
        slide,
        left: float,
        top: float,
        width: float,
        height: float,
        color: str,
        shape_type=MSO_SHAPE.RECTANGLE
    ):
        """Fügt eine Form hinzu."""
        shape = slide.shapes.add_shape(
            shape_type,
            Inches(left), Inches(top),
            Inches(width), Inches(height)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = self._hex_to_rgb(color)
        shape.line.fill.background()
        return shape
    
    def _add_text_box(
        self,
        slide,
        left: float,
        top: float,
        width: float,
        height: float,
        text: str,
        font_size: int = 14,
        font_color: str = None,
        bold: bool = False,
        align: PP_ALIGN = PP_ALIGN.LEFT,
        font_name: str = "Calibri"
    ):
        """Fügt eine Textbox hinzu."""
        if font_color is None:
            font_color = self.palette["text"]
        
        txBox = slide.shapes.add_textbox(
            Inches(left), Inches(top),
            Inches(width), Inches(height)
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = self._hex_to_rgb(font_color)
        p.font.bold = bold
        p.font.name = font_name
        p.alignment = align
        
        return txBox
    
    def _add_slide_number(self, slide, number: int):
        """Fügt Seitenzahl hinzu."""
        if not self.include_slide_numbers:
            return
        
        self._add_text_box(
            slide,
            left=12.5, top=7.0,
            width=0.7, height=0.3,
            text=f"{number}/{self.total_slides}",
            font_size=10,
            font_color=self.palette["text_light"],
            align=PP_ALIGN.RIGHT
        )
    
    def _add_footer(self, slide, text: str = None):
        """Fügt Footer mit Firmenname hinzu."""
        if text is None:
            text = self.company_name
        if not text:
            return
        
        self._add_text_box(
            slide,
            left=0.5, top=7.0,
            width=4, height=0.3,
            text=text,
            font_size=10,
            font_color=self.palette["text_light"]
        )
    
    # ========================================
    # SLIDE RENDERER
    # ========================================
    
    def _render_title_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Titel-Slide (Deckblatt).
        
        Layout:
        - Großer Titel zentriert
        - Untertitel/Firma
        - Datum
        - Optional: Logo
        """
        self._add_background(slide, self.palette["primary"])
        
        # Dekorative Linie
        self._add_shape(slide, 1, 3.2, 11.333, 0.02, self.palette["accent"])
        
        # Haupttitel
        title = data.get("title", "Präsentation")
        self._add_text_box(
            slide,
            left=1, top=2.0,
            width=11.333, height=1.2,
            text=title,
            font_size=44,
            font_color="#FFFFFF",
            bold=True,
            align=PP_ALIGN.CENTER
        )
        
        # Untertitel / Firma
        subtitle = data.get("subtitle", self.company_name)
        if subtitle:
            self._add_text_box(
                slide,
                left=1, top=3.5,
                width=11.333, height=0.6,
                text=subtitle,
                font_size=24,
                font_color="#FFFFFF",
                align=PP_ALIGN.CENTER
            )
        
        # Datum
        date_str = data.get("date", datetime.now().strftime("%B %Y"))
        self._add_text_box(
            slide,
            left=1, top=6.5,
            width=11.333, height=0.4,
            text=date_str,
            font_size=14,
            font_color=self.palette["secondary"],
            align=PP_ALIGN.CENTER
        )
    
    def _render_chapter_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Kapitel-Slide (Section Opener).
        
        Layout:
        - Dunkler Hintergrund
        - Großer Kapitel-Titel
        - Optional: Kapitel-Nummer
        - Dekorative Elemente
        """
        self._add_background(slide, self.palette["chapter_bg"])
        
        # Akzent-Streifen links
        self._add_shape(slide, 0, 0, 0.15, 7.5, self.palette["accent"])
        
        # Kapitel-Nummer (falls vorhanden)
        chapter_num = data.get("chapter_number", "")
        if chapter_num:
            self._add_text_box(
                slide,
                left=1, top=2.0,
                width=11, height=0.6,
                text=f"KAPITEL {chapter_num}",
                font_size=16,
                font_color=self.palette["accent"],
                bold=True
            )
        
        # Kapitel-Titel
        title = data.get("title", "Neues Kapitel")
        self._add_text_box(
            slide,
            left=1, top=2.8,
            width=11, height=1.5,
            text=title,
            font_size=48,
            font_color="#FFFFFF",
            bold=True
        )
        
        # Untertitel / Beschreibung
        subtitle = data.get("subtitle", "")
        if subtitle:
            self._add_text_box(
                slide,
                left=1, top=4.5,
                width=10, height=1.0,
                text=subtitle,
                font_size=18,
                font_color=self.palette["secondary"]
            )
        
        self.current_chapter = title
    
    def _render_executive_summary(self, slide, data: Dict[str, Any], number: int):
        """
        Executive Summary - 2-Spalten Layout.
        
        Layout:
        - Titel oben
        - Linke Spalte: Key Points
        - Rechte Spalte: Highlights oder Metrics
        """
        self._add_background(slide)
        
        # Titel
        title = data.get("title", "Executive Summary")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=32, bold=True,
            font_color=self.palette["primary"]
        )
        
        # Trennlinie
        self._add_shape(slide, 0.5, 1.1, 12, 0.02, self.palette["accent"])
        
        bullets = data.get("bullets", [])
        content = data.get("content", "")
        
        # Linke Spalte - Key Points
        if bullets:
            y_pos = 1.5
            for i, bullet in enumerate(bullets[:4]):
                # Nummer-Badge
                self._add_shape(slide, 0.5, y_pos, 0.4, 0.4, self.palette["primary"])
                self._add_text_box(
                    slide, left=0.5, top=y_pos, width=0.4, height=0.4,
                    text=str(i + 1), font_size=14, font_color="#FFFFFF",
                    bold=True, align=PP_ALIGN.CENTER
                )
                
                # Bullet Text
                self._add_text_box(
                    slide, left=1.1, top=y_pos, width=5.5, height=1.2,
                    text=bullet, font_size=14, font_color=self.palette["text"]
                )
                y_pos += 1.4
        
        # Rechte Spalte - Highlights Box
        self._add_shape(slide, 7, 1.5, 5.5, 5, self.palette["primary"])
        
        highlights = data.get("highlights", bullets[4:] if len(bullets) > 4 else [])
        if highlights:
            self._add_text_box(
                slide, left=7.3, top=1.7, width=5, height=0.5,
                text="KEY HIGHLIGHTS", font_size=14, font_color="#FFFFFF", bold=True
            )
            
            y_pos = 2.4
            for highlight in highlights[:4]:
                self._add_text_box(
                    slide, left=7.3, top=y_pos, width=4.8, height=1.0,
                    text=f"• {highlight}", font_size=13, font_color="#FFFFFF"
                )
                y_pos += 1.1
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_bullets_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Standard Bullet-Slide.
        
        Layout:
        - Titel oben
        - 4-6 Bullets mit Icons/Nummern
        - Optional: Sidebar mit Zusatzinfo
        """
        self._add_background(slide)
        
        # Akzent-Streifen oben
        self._add_shape(slide, 0, 0, 13.333, 0.08, self.palette["primary"])
        
        # Titel
        title = data.get("title", "Inhalt")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        bullets = data.get("bullets", [])
        if not bullets:
            # Fallback: Content als einzelnen Bullet
            content = data.get("content", "")
            if content:
                bullets = [content]
        
        # Bullets rendern
        y_pos = 1.4
        for i, bullet in enumerate(bullets[:6]):
            if not bullet or len(bullet.strip()) < 3:
                continue
            
            # Bullet-Punkt (Kreis)
            self._add_shape(
                slide, 0.5, y_pos + 0.15, 0.15, 0.15,
                self.palette["accent"],
                MSO_SHAPE.OVAL
            )
            
            # Bullet-Text
            self._add_text_box(
                slide, left=0.85, top=y_pos, width=11.5, height=0.9,
                text=bullet, font_size=16, font_color=self.palette["text"]
            )
            y_pos += 1.0
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_text_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Text-Slide für ausführliche Erklärungen.
        
        Layout:
        - Titel oben
        - Fließtext (mehrere Absätze)
        - Optional: Hervorhebungs-Box
        """
        self._add_background(slide)
        
        # Akzent-Streifen
        self._add_shape(slide, 0, 0, 0.08, 7.5, self.palette["primary"])
        
        # Titel
        title = data.get("title", "Details")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        # Content - entweder aus 'content' oder aus 'bullets' zusammengesetzt
        content = data.get("content", "")
        if not content:
            bullets = data.get("bullets", [])
            if bullets:
                # Bullets zu Fließtext konvertieren
                content = "\n\n".join(bullets)
        
        if content:
            self._add_text_box(
                slide, left=0.5, top=1.3, width=12, height=5.5,
                text=content, font_size=15, font_color=self.palette["text"]
            )
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_persona_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Persona-Steckbrief.
        
        Layout:
        - Avatar-Bereich links
        - Name, Rolle, Unternehmen
        - Eigenschaften (Alter, Position, etc.)
        - Pain Points / Goals
        - Zitat
        """
        self._add_background(slide)
        
        # Titel-Bereich
        self._add_shape(slide, 0, 0, 13.333, 1.0, self.palette["primary"])
        
        title = data.get("title", "Persona")
        self._add_text_box(
            slide, left=0.5, top=0.25, width=12, height=0.6,
            text=title, font_size=24, bold=True, font_color="#FFFFFF"
        )
        
        # Avatar-Platzhalter (Kreis)
        self._add_shape(slide, 0.5, 1.3, 2.5, 2.5, self.palette["secondary"], MSO_SHAPE.OVAL)
        
        # Persona-Details aus Bullets extrahieren
        bullets = data.get("bullets", [])
        name = data.get("persona_name", "")
        role = data.get("persona_role", "")
        
        # Name und Rolle
        if not name and bullets:
            name = bullets[0] if bullets else "Max Mustermann"
        if not role and len(bullets) > 1:
            role = bullets[1] if len(bullets) > 1 else "Entscheider"
        
        self._add_text_box(
            slide, left=3.3, top=1.3, width=4, height=0.5,
            text=name, font_size=22, bold=True, font_color=self.palette["primary"]
        )
        self._add_text_box(
            slide, left=3.3, top=1.85, width=4, height=0.4,
            text=role, font_size=16, font_color=self.palette["text_light"]
        )
        
        # Eigenschaften
        properties_y = 2.5
        properties = bullets[2:6] if len(bullets) > 2 else []
        for prop in properties:
            self._add_text_box(
                slide, left=3.3, top=properties_y, width=4, height=0.4,
                text=f"• {prop}", font_size=12, font_color=self.palette["text"]
            )
            properties_y += 0.4
        
        # Pain Points Box (rechts)
        self._add_shape(slide, 8, 1.3, 4.8, 2.8, "#FEF2F2")  # Rot-getönt
        self._add_text_box(
            slide, left=8.2, top=1.4, width=4.4, height=0.4,
            text="PAIN POINTS", font_size=12, bold=True, font_color="#DC2626"
        )
        
        pain_points = data.get("pain_points", bullets[6:9] if len(bullets) > 6 else [])
        pain_y = 1.9
        for pain in pain_points[:3]:
            self._add_text_box(
                slide, left=8.2, top=pain_y, width=4.4, height=0.6,
                text=f"• {pain}", font_size=11, font_color="#7F1D1D"
            )
            pain_y += 0.55
        
        # Goals Box (rechts unten)
        self._add_shape(slide, 8, 4.3, 4.8, 2.5, "#F0FDF4")  # Grün-getönt
        self._add_text_box(
            slide, left=8.2, top=4.4, width=4.4, height=0.4,
            text="GOALS", font_size=12, bold=True, font_color="#16A34A"
        )
        
        goals = data.get("goals", bullets[9:12] if len(bullets) > 9 else [])
        goal_y = 4.9
        for goal in goals[:3]:
            self._add_text_box(
                slide, left=8.2, top=goal_y, width=4.4, height=0.6,
                text=f"• {goal}", font_size=11, font_color="#166534"
            )
            goal_y += 0.55
        
        # Zitat unten
        quote = data.get("quote", "")
        if not quote and len(bullets) > 12:
            quote = bullets[12]
        if quote:
            self._add_text_box(
                slide, left=0.5, top=6.0, width=7, height=0.8,
                text=f'"{quote}"', font_size=13, font_color=self.palette["text_light"],
                align=PP_ALIGN.LEFT
            )
        
        self._add_slide_number(slide, number)
    
    def _render_comparison_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Vergleichs-Slide (z.B. für Wettbewerber, Optionen).
        
        Layout:
        - Titel
        - 2-4 Spalten für Vergleich
        - Highlight für "unsere" Option
        """
        self._add_background(slide)
        
        # Titel
        title = data.get("title", "Vergleich")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        bullets = data.get("bullets", [])
        columns = data.get("columns", 3)
        
        # Spalten-Breite berechnen
        total_width = 12.333
        col_width = total_width / columns
        
        # Header-Zeile (falls vorhanden)
        headers = data.get("headers", [])
        if not headers and bullets:
            # Versuche Headers aus ersten Bullets zu extrahieren
            headers = [f"Option {i+1}" for i in range(columns)]
        
        # Spalten rendern
        for col in range(min(columns, len(headers) if headers else columns)):
            x_pos = 0.5 + col * col_width
            
            # Spalten-Hintergrund (mittlere Spalte hervorgehoben)
            bg_color = self.palette["primary"] if col == 1 else "#F3F4F6"
            text_color = "#FFFFFF" if col == 1 else self.palette["text"]
            
            self._add_shape(slide, x_pos, 1.3, col_width - 0.2, 5.5, bg_color)
            
            # Header
            header = headers[col] if col < len(headers) else f"Option {col+1}"
            self._add_text_box(
                slide, left=x_pos + 0.1, top=1.4, width=col_width - 0.4, height=0.5,
                text=header, font_size=16, bold=True, font_color=text_color,
                align=PP_ALIGN.CENTER
            )
            
            # Spalten-Inhalt aus Bullets
            col_bullets = bullets[col::columns] if bullets else []
            y_pos = 2.2
            for item in col_bullets[:6]:
                self._add_text_box(
                    slide, left=x_pos + 0.1, top=y_pos, width=col_width - 0.4, height=0.7,
                    text=f"• {item}", font_size=12, font_color=text_color
                )
                y_pos += 0.8
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_chart_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Chart/Daten-Slide.
        
        Layout:
        - Titel
        - Chart-Platzhalter (für echte Charts oder Bild)
        - Key Insights rechts
        """
        self._add_background(slide)
        
        # Titel
        title = data.get("title", "Daten & Analyse")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        # Chart-Platzhalter (links, 60% der Breite)
        self._add_shape(slide, 0.5, 1.3, 7.5, 5.2, "#F9FAFB")
        self._add_text_box(
            slide, left=2.5, top=3.5, width=3.5, height=0.5,
            text="[CHART]", font_size=24, font_color=self.palette["text_light"],
            align=PP_ALIGN.CENTER
        )
        
        # Insights-Box (rechts)
        self._add_shape(slide, 8.2, 1.3, 4.6, 5.2, self.palette["primary"])
        self._add_text_box(
            slide, left=8.4, top=1.5, width=4.2, height=0.4,
            text="KEY INSIGHTS", font_size=14, bold=True, font_color="#FFFFFF"
        )
        
        bullets = data.get("bullets", [])
        y_pos = 2.1
        for bullet in bullets[:5]:
            self._add_text_box(
                slide, left=8.4, top=y_pos, width=4.2, height=0.9,
                text=f"→ {bullet}", font_size=12, font_color="#FFFFFF"
            )
            y_pos += 0.95
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_timeline_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Timeline/Roadmap-Slide.
        
        Layout:
        - Titel
        - Horizontale Timeline mit Meilensteinen
        """
        self._add_background(slide)
        
        # Titel
        title = data.get("title", "Roadmap")
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text=title, font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        bullets = data.get("bullets", [])
        phases = data.get("phases", bullets[:6])
        
        # Timeline-Linie
        self._add_shape(slide, 0.5, 3.5, 12.333, 0.05, self.palette["secondary"])
        
        # Meilensteine
        num_phases = min(len(phases), 6)
        if num_phases == 0:
            num_phases = 4
            phases = [f"Phase {i+1}" for i in range(4)]
        
        phase_width = 12.333 / num_phases
        
        for i, phase in enumerate(phases[:num_phases]):
            x_pos = 0.5 + i * phase_width + phase_width / 2 - 0.25
            
            # Kreis auf Timeline
            self._add_shape(
                slide, x_pos, 3.35, 0.5, 0.5,
                self.palette["primary"] if i % 2 == 0 else self.palette["accent"],
                MSO_SHAPE.OVAL
            )
            
            # Phase-Label (alternierend oben/unten)
            y_offset = 1.8 if i % 2 == 0 else 4.2
            
            self._add_text_box(
                slide, left=x_pos - 1, top=y_offset, width=2.5, height=1.2,
                text=phase, font_size=12, font_color=self.palette["text"],
                align=PP_ALIGN.CENTER
            )
        
        self._add_slide_number(slide, number)
        self._add_footer(slide)
    
    def _render_quote_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Zitat/Testimonial-Slide.
        
        Layout:
        - Großes Zitat zentriert
        - Quelle/Autor
        """
        self._add_background(slide, self.palette["chapter_bg"])
        
        # Große Anführungszeichen
        self._add_text_box(
            slide, left=1, top=1.5, width=2, height=1.5,
            text=""", font_size=120, font_color=self.palette["accent"],
            bold=True
        )
        
        # Zitat
        bullets = data.get("bullets", [])
        quote = data.get("quote", bullets[0] if bullets else "Zitat hier")
        
        self._add_text_box(
            slide, left=1.5, top=2.5, width=10, height=3,
            text=quote, font_size=28, font_color="#FFFFFF",
            align=PP_ALIGN.CENTER
        )
        
        # Quelle
        source = data.get("source", bullets[1] if len(bullets) > 1 else "")
        if source:
            self._add_text_box(
                slide, left=1.5, top=5.8, width=10, height=0.5,
                text=f"— {source}", font_size=16, font_color=self.palette["secondary"],
                align=PP_ALIGN.CENTER
            )
        
        self._add_slide_number(slide, number)
    
    def _render_conclusion_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Fazit/Key Takeaways Slide.
        
        Layout:
        - Titel
        - Nummerierte Key Takeaways
        - Call to Action
        """
        self._add_background(slide)
        
        # Akzent-Streifen
        self._add_shape(slide, 0, 0, 13.333, 0.15, self.palette["accent"])
        
        # Titel
        title = data.get("title", "Key Takeaways")
        self._add_text_box(
            slide, left=0.5, top=0.5, width=12, height=0.7,
            text=title, font_size=32, bold=True,
            font_color=self.palette["primary"]
        )
        
        bullets = data.get("bullets", [])
        
        # Nummerierte Takeaways
        y_pos = 1.5
        for i, bullet in enumerate(bullets[:5], 1):
            # Nummer-Box
            self._add_shape(slide, 0.5, y_pos, 0.6, 0.6, self.palette["primary"])
            self._add_text_box(
                slide, left=0.5, top=y_pos + 0.05, width=0.6, height=0.5,
                text=str(i), font_size=20, bold=True, font_color="#FFFFFF",
                align=PP_ALIGN.CENTER
            )
            
            # Takeaway Text
            self._add_text_box(
                slide, left=1.3, top=y_pos, width=11, height=0.9,
                text=bullet, font_size=16, font_color=self.palette["text"]
            )
            y_pos += 1.1
        
        # Call to Action (falls vorhanden)
        cta = data.get("cta", "")
        if cta or len(bullets) > 5:
            cta = cta or bullets[5]
            self._add_shape(slide, 0.5, 6.3, 12.333, 0.8, self.palette["accent"])
            self._add_text_box(
                slide, left=0.5, top=6.4, width=12.333, height=0.6,
                text=cta, font_size=18, bold=True, font_color="#FFFFFF",
                align=PP_ALIGN.CENTER
            )
        
        self._add_slide_number(slide, number)
    
    def _render_contact_slide(self, slide, data: Dict[str, Any], number: int):
        """
        Kontakt-Slide.
        
        Layout:
        - Großer "Danke" / "Fragen?" Text
        - Kontaktinformationen
        - Logo-Platzhalter
        """
        self._add_background(slide, self.palette["primary"])
        
        # Haupttext
        title = data.get("title", "Vielen Dank!")
        self._add_text_box(
            slide, left=1, top=2, width=11.333, height=1.2,
            text=title, font_size=48, bold=True, font_color="#FFFFFF",
            align=PP_ALIGN.CENTER
        )
        
        # Untertitel
        subtitle = data.get("subtitle", "Fragen & Diskussion")
        self._add_text_box(
            slide, left=1, top=3.3, width=11.333, height=0.6,
            text=subtitle, font_size=24, font_color=self.palette["secondary"],
            align=PP_ALIGN.CENTER
        )
        
        # Kontakt-Box
        bullets = data.get("bullets", [])
        if bullets or self.company_name:
            self._add_shape(slide, 4, 4.5, 5.333, 2, "rgba(255,255,255,0.1)")
            
            contact_text = self.company_name
            if bullets:
                contact_text = "\n".join(bullets[:3])
            
            self._add_text_box(
                slide, left=4.2, top=4.7, width=4.933, height=1.6,
                text=contact_text, font_size=14, font_color="#FFFFFF",
                align=PP_ALIGN.CENTER
            )
    
    # ========================================
    # HAUPTMETHODEN
    # ========================================
    
    def create_presentation(
        self,
        slides: List[Dict[str, Any]],
        title: str = "Präsentation",
        company: str = "",
        include_sources_slide: bool = False
    ) -> bytes:
        """
        Erstellt eine komplette Präsentation.
        
        Args:
            slides: Liste von Slide-Daten
            title: Präsentationstitel
            company: Firmenname
            include_sources_slide: Quellenverzeichnis am Ende
        
        Returns:
            PPTX als Bytes
        """
        self.company_name = company or self.company_name
        self.total_slides = len(slides) + (1 if include_sources_slide else 0)
        
        all_sources = []
        
        for i, slide_data in enumerate(slides, 1):
            # Slide-Typ bestimmen
            slide_type = slide_data.get("type", "bullets")
            
            # Automatische Typ-Erkennung falls nötig
            if slide_type not in self.SLIDE_RENDERERS:
                slide_type = self._detect_slide_type(slide_data)
            
            # Neuen Slide hinzufügen
            slide_layout = self.prs.slide_layouts[6]  # Blank layout
            slide = self.prs.slides.add_slide(slide_layout)
            
            # Renderer aufrufen
            renderer_name = self.SLIDE_RENDERERS.get(slide_type, "_render_bullets_slide")
            renderer = getattr(self, renderer_name, self._render_bullets_slide)
            
            try:
                renderer(slide, slide_data, i)
            except Exception as e:
                logger.error(f"Error rendering slide {i} ({slide_type}): {e}")
                # Fallback zu Bullets
                self._render_bullets_slide(slide, slide_data, i)
            
            # Quellen sammeln
            if slide_data.get("sources"):
                all_sources.extend(slide_data["sources"])
        
        # Quellenverzeichnis
        if include_sources_slide and all_sources:
            self._add_sources_slide(list(set(all_sources)))
        
        # Als Bytes zurückgeben
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        return output.read()
    
    def _detect_slide_type(self, slide_data: Dict[str, Any]) -> str:
        """
        Erkennt automatisch den besten Slide-Typ basierend auf Content.
        """
        title = slide_data.get("title", "").lower()
        bullets = slide_data.get("bullets", [])
        content = slide_data.get("content", "")
        
        # Keyword-basierte Erkennung
        if any(kw in title for kw in ["persona", "zielgruppe", "profil"]):
            return "persona"
        if any(kw in title for kw in ["vergleich", "comparison", "vs", "matrix"]):
            return "comparison"
        if any(kw in title for kw in ["timeline", "roadmap", "meilenstein", "phase"]):
            return "timeline"
        if any(kw in title for kw in ["zitat", "testimonial", "referenz"]):
            return "quote"
        if any(kw in title for kw in ["fazit", "conclusion", "takeaway", "zusammenfassung"]):
            return "conclusion"
        if any(kw in title for kw in ["kontakt", "fragen", "danke"]):
            return "contact"
        if any(kw in title for kw in ["kapitel", "chapter", "teil"]):
            return "chapter"
        
        # Content-Länge basierte Erkennung
        total_text = len(" ".join(bullets)) + len(content)
        if total_text > 800:
            return "text"  # Langer Content → Text-Slide
        
        return "bullets"
    
    def _add_sources_slide(self, sources: List[str]):
        """Fügt Quellenverzeichnis hinzu."""
        slide_layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(slide_layout)
        
        self._add_background(slide)
        
        self._add_text_box(
            slide, left=0.5, top=0.4, width=12, height=0.7,
            text="Quellen", font_size=28, bold=True,
            font_color=self.palette["primary"]
        )
        
        y_pos = 1.3
        for source in sources[:15]:
            self._add_text_box(
                slide, left=0.5, top=y_pos, width=12, height=0.35,
                text=f"• {source}", font_size=10, font_color=self.palette["text_light"]
            )
            y_pos += 0.38


def create_presentation_v3(
    slides: List[Dict[str, Any]],
    title: str = "Präsentation",
    company: str = "",
    colors: Dict[str, str] = None,
    palette: str = "corporate"
) -> bytes:
    """
    Convenience-Funktion zum Erstellen einer Präsentation.
    
    Args:
        slides: Liste von Slide-Daten
        title: Präsentationstitel
        company: Firmenname
        colors: Custom Farben
        palette: Farbpalette
    
    Returns:
        PPTX als Bytes
    """
    designer = PPTXDesignerV3(colors=colors, palette=palette, company_name=company)
    return designer.create_presentation(slides, title, company)
