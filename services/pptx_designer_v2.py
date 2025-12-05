"""
PPTX Designer Service v2 für Stratgen.
- Nutzt Wizard-Farbauswahl
- Fügt Quellenangaben hinzu
- Professionelle Layouts
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import json

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))


class PPTXDesignerV2:
    """Erstellt professionelle PPTX-Präsentationen mit Wizard-Farben und Quellen."""
    
    # Fallback-Paletten
    PALETTES = {
        "corporate": {
            "primary": "#1E40AF",
            "secondary": "#3B82F6", 
            "accent": "#10B981",
            "background": "#FFFFFF",
            "text": "#111827"
        },
        "modern": {
            "primary": "#7C3AED",
            "secondary": "#A78BFA",
            "accent": "#F59E0B",
            "background": "#FAFAFA",
            "text": "#27272A"
        },
        "minimal": {
            "primary": "#000000",
            "secondary": "#525252",
            "accent": "#3B82F6",
            "background": "#FFFFFF",
            "text": "#262626"
        },
        "vibrant": {
            "primary": "#EC4899",
            "secondary": "#8B5CF6",
            "accent": "#06B6D4",
            "background": "#FDF4FF",
            "text": "#581C87"
        }
    }
    
    def __init__(self, colors: Dict[str, str] = None, palette: str = "corporate"):
        """
        Args:
            colors: Wizard-Farben dict mit primary, secondary, accent, background, text
            palette: Fallback-Palette wenn keine Farben übergeben
        """
        if colors:
            self.colors = {
                "primary": colors.get("primary", "#1E40AF"),
                "secondary": colors.get("secondary", "#3B82F6"),
                "accent": colors.get("accent", "#10B981"),
                "background": colors.get("background", "#FFFFFF"),
                "text": colors.get("text", "#111827")
            }
        else:
            self.colors = self.PALETTES.get(palette, self.PALETTES["corporate"])
        
        self.prs = None
        self.slide_sources = []  # Sammelt Quellen pro Slide
    
    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Konvertiert Hex zu RGB."""
        hex_color = hex_color.lstrip('#')
        return RGBColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    def _add_source_footer(self, slide, sources: List[str]):
        """Fügt Quellenangaben als Footer hinzu."""
        if not sources:
            return
        
        # Formatiere Quellen
        source_text = "Quellen: " + " | ".join(sources[:3])  # Max 3 Quellen
        if len(sources) > 3:
            source_text += f" (+{len(sources)-3} weitere)"
        
        # Footer Box
        footer = slide.shapes.add_textbox(
            Inches(0.5), Inches(7.1), Inches(12.333), Inches(0.3)
        )
        tf = footer.text_frame
        p = tf.paragraphs[0]
        p.text = source_text
        p.font.size = Pt(8)
        p.font.color.rgb = self._hex_to_rgb(self.colors.get("secondary", "#666666"))
        p.alignment = PP_ALIGN.LEFT
    
    def _add_slide_number(self, slide, number: int, total: int):
        """Fügt Seitenzahl hinzu."""
        num_box = slide.shapes.add_textbox(
            Inches(12.5), Inches(7.1), Inches(0.7), Inches(0.3)
        )
        tf = num_box.text_frame
        p = tf.paragraphs[0]
        p.text = f"{number}/{total}"
        p.font.size = Pt(9)
        p.font.color.rgb = self._hex_to_rgb(self.colors.get("secondary", "#666666"))
        p.alignment = PP_ALIGN.RIGHT
    
    def create_presentation(self, slides: List[Dict], 
                           title: str = "Präsentation",
                           company: str = "",
                           include_sources_slide: bool = True) -> bytes:
        """
        Erstellt eine komplette PPTX-Präsentation.
        
        Args:
            slides: Liste von Slide-Dicts mit type, title, content, sources
            title: Titel der Präsentation
            company: Firmenname für Footer
            include_sources_slide: Fügt am Ende eine Quellenübersicht hinzu
        
        Returns:
            PPTX als Bytes
        """
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)  # 16:9
        self.prs.slide_height = Inches(7.5)
        
        all_sources = []
        total_slides = len(slides) + (1 if include_sources_slide else 0)
        
        for i, slide_data in enumerate(slides):
            slide_type = slide_data.get("type", "content")
            sources = slide_data.get("sources", [])
            all_sources.extend(sources)
            
            # Erstelle Slide basierend auf Typ
            if slide_type == "title" or i == 0:
                slide = self._add_title_slide(slide_data, company)
            elif slide_type == "section":
                slide = self._add_section_slide(slide_data)
            elif slide_type == "two_column":
                slide = self._add_two_column_slide(slide_data)
            elif slide_type == "bullets":
                slide = self._add_bullet_slide(slide_data)
            elif slide_type == "quote":
                slide = self._add_quote_slide(slide_data)
            elif slide_type == "data" or slide_type == "chart":
                slide = self._add_data_slide(slide_data)
            else:
                slide = self._add_content_slide(slide_data)
            
            # Füge Quellen-Footer hinzu (außer bei Title-Slide)
            if sources and slide_type != "title":
                self._add_source_footer(slide, sources)
            
            # Seitenzahl (außer bei Title-Slide)
            if slide_type != "title":
                self._add_slide_number(slide, i + 1, total_slides)
        
        # Quellenübersicht am Ende
        if include_sources_slide and all_sources:
            self._add_sources_overview_slide(list(set(all_sources)))
        
        # Speichere als Bytes
        from io import BytesIO
        buffer = BytesIO()
        self.prs.save(buffer)
        buffer.seek(0)
        return buffer.read()
    
    def _add_background(self, slide, use_primary: bool = False):
        """Fügt Hintergrundfarbe hinzu."""
        background = slide.background
        fill = background.fill
        fill.solid()
        color_key = "primary" if use_primary else "background"
        fill.fore_color.rgb = self._hex_to_rgb(self.colors[color_key])
    
    def _add_title_slide(self, data: Dict, company: str = ""):
        """Erstellt Title-Slide."""
        layout = self.prs.slide_layouts[6]  # Blank
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide, use_primary=True)
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(2.5), Inches(12.333), Inches(1.5)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(54)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
        p.alignment = PP_ALIGN.CENTER
        
        # Subtitle
        if data.get("subtitle"):
            sub_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(4.2), Inches(12.333), Inches(1)
            )
            tf = sub_box.text_frame
            p = tf.paragraphs[0]
            p.text = data.get("subtitle", "")
            p.font.size = Pt(24)
            p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
            p.alignment = PP_ALIGN.CENTER
        
        # Accent line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(5.5), Inches(4), Inches(2.333), Inches(0.05)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = self._hex_to_rgb(self.colors["accent"])
        line.line.fill.background()
        
        # Company name
        if company:
            comp_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(6.5), Inches(12.333), Inches(0.5)
            )
            tf = comp_box.text_frame
            p = tf.paragraphs[0]
            p.text = company
            p.font.size = Pt(14)
            p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
            p.alignment = PP_ALIGN.CENTER
        
        return slide
    
    def _add_section_slide(self, data: Dict):
        """Erstellt Section-Divider-Slide."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Sekundäre Farbe als Hintergrund
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self._hex_to_rgb(self.colors["secondary"])
        
        # Section Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(3), Inches(12.333), Inches(1.5)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(48)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
        p.alignment = PP_ALIGN.CENTER
        
        return slide
    
    def _add_content_slide(self, data: Dict):
        """Erstellt Content-Slide mit Titel und Text."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide)
        
        # Accent bar oben
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.333), Inches(0.1)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors["primary"])
        bar.line.fill.background()
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.5), Inches(11.833), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Content
        content = data.get("content", "") or data.get("body", "")
        if content:
            content_box = slide.shapes.add_textbox(
                Inches(0.75), Inches(1.5), Inches(11.833), Inches(5.2)
            )
            tf = content_box.text_frame
            tf.word_wrap = True
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()
                
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    p.text = "• " + line[2:]
                    p.level = 0
                else:
                    p.text = line
                
                p.font.size = Pt(18)
                p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
                p.space_after = Pt(12)
        
        return slide
    
    def _add_bullet_slide(self, data: Dict):
        """Erstellt Bullet-Point-Slide."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide)
        
        # Accent bar links
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(0.15), Inches(7.5)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors["primary"])
        bar.line.fill.background()
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.5), Inches(11.833), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Bullets
        bullets = data.get("bullets", [])
        if not bullets and data.get("content"):
            bullets = [l.strip().lstrip('- *') for l in data["content"].split('\n') if l.strip()]
        
        if bullets:
            content_box = slide.shapes.add_textbox(
                Inches(0.75), Inches(1.5), Inches(11.833), Inches(5.2)
            )
            tf = content_box.text_frame
            
            for i, bullet in enumerate(bullets):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()
                
                p.text = "• " + bullet
                p.font.size = Pt(20)
                p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
                p.space_after = Pt(16)
        
        return slide
    
    def _add_two_column_slide(self, data: Dict):
        """Erstellt Two-Column-Slide."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide)
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.5), Inches(11.833), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Left Column
        left_content = data.get("left_content", "")
        if not left_content and data.get("content"):
            left_content = data["content"][:len(data["content"])//2]
        
        left_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(1.5), Inches(5.5), Inches(5.2)
        )
        tf = left_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = left_content
        p.font.size = Pt(16)
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Right Column
        right_box = slide.shapes.add_textbox(
            Inches(7.083), Inches(1.5), Inches(5.5), Inches(5.2)
        )
        tf = right_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = data.get("right_content", "")
        p.font.size = Pt(16)
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Divider line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(6.583), Inches(1.5), Inches(0.02), Inches(5)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = self._hex_to_rgb(self.colors["secondary"])
        line.line.fill.background()
        
        return slide
    
    def _add_quote_slide(self, data: Dict):
        """Erstellt Quote-Slide."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Dunkler Hintergrund
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Quote marks
        quote_mark = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.5), Inches(2), Inches(1.5)
        )
        tf = quote_mark.text_frame
        p = tf.paragraphs[0]
        p.text = '"'
        p.font.size = Pt(120)
        p.font.color.rgb = self._hex_to_rgb(self.colors["accent"])
        
        # Quote text
        quote_box = slide.shapes.add_textbox(
            Inches(1), Inches(2.5), Inches(11.333), Inches(3)
        )
        tf = quote_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = data.get("quote", data.get("content", ""))
        p.font.size = Pt(28)
        p.font.italic = True
        p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
        p.alignment = PP_ALIGN.CENTER
        
        # Attribution
        if data.get("author"):
            attr_box = slide.shapes.add_textbox(
                Inches(1), Inches(5.5), Inches(11.333), Inches(0.5)
            )
            tf = attr_box.text_frame
            p = tf.paragraphs[0]
            p.text = f"— {data['author']}"
            p.font.size = Pt(18)
            p.font.color.rgb = self._hex_to_rgb(self.colors["secondary"])
            p.alignment = PP_ALIGN.CENTER
        
        return slide
    
    def _add_data_slide(self, data: Dict):
        """Erstellt Daten/Chart-Slide mit Platzhalter."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide)
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.5), Inches(11.833), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data.get("title", "Daten")
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Data points
        data_points = data.get("data_points", [])
        if data_points:
            y_pos = 1.8
            for dp in data_points[:4]:  # Max 4 Data Points
                # Value box
                val_box = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(1), Inches(y_pos), Inches(3), Inches(1.2)
                )
                val_box.fill.solid()
                val_box.fill.fore_color.rgb = self._hex_to_rgb(self.colors["primary"])
                
                # Value text
                tf = val_box.text_frame
                tf.word_wrap = False
                p = tf.paragraphs[0]
                p.text = str(dp.get("value", ""))
                p.font.size = Pt(36)
                p.font.bold = True
                p.font.color.rgb = self._hex_to_rgb("#FFFFFF")
                p.alignment = PP_ALIGN.CENTER
                
                # Label
                label_box = slide.shapes.add_textbox(
                    Inches(4.5), Inches(y_pos + 0.3), Inches(8), Inches(0.6)
                )
                tf = label_box.text_frame
                p = tf.paragraphs[0]
                p.text = dp.get("label", "")
                p.font.size = Pt(20)
                p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
                
                y_pos += 1.4
        else:
            # Fallback: Zeige Content als Text
            content = data.get("content", "")
            if content:
                content_box = slide.shapes.add_textbox(
                    Inches(0.75), Inches(1.5), Inches(11.833), Inches(5.2)
                )
                tf = content_box.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.text = content
                p.font.size = Pt(18)
                p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        return slide
    
    def _add_sources_overview_slide(self, sources: List[str]):
        """Erstellt Quellenübersicht-Slide am Ende."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        self._add_background(slide)
        
        # Accent bar
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0), Inches(13.333), Inches(0.1)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors["primary"])
        bar.line.fill.background()
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.5), Inches(11.833), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = "Quellen & Referenzen"
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
        
        # Sources list
        content_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(1.5), Inches(11.833), Inches(5.5)
        )
        tf = content_box.text_frame
        
        for i, source in enumerate(sources[:15]):  # Max 15 Quellen
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            
            p.text = f"• {source}"
            p.font.size = Pt(14)
            p.font.color.rgb = self._hex_to_rgb(self.colors["text"])
            p.space_after = Pt(8)
        
        if len(sources) > 15:
            p = tf.add_paragraph()
            p.text = f"... und {len(sources) - 15} weitere Quellen"
            p.font.size = Pt(12)
            p.font.color.rgb = self._hex_to_rgb(self.colors["secondary"])
        
        return slide


def create_presentation_v2(slides: List[Dict], 
                          title: str = "Präsentation",
                          company: str = "",
                          colors: Dict[str, str] = None,
                          palette: str = "corporate",
                          include_sources: bool = True) -> bytes:
    """
    Erstellt PPTX mit Wizard-Farben und Quellenangaben.
    
    Args:
        slides: Liste von Slide-Dicts mit type, title, content, sources
        title: Präsentationstitel
        company: Firmenname
        colors: Wizard-Farben (primary, secondary, accent, background, text)
        palette: Fallback-Palette
        include_sources: Quellenübersicht am Ende
    
    Returns:
        PPTX als Bytes
    """
    designer = PPTXDesignerV2(colors=colors, palette=palette)
    return designer.create_presentation(slides, title, company, include_sources)
