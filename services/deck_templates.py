# services/deck_templates.py
from pptx.dml.color import RGBColor
from pptx.util import Pt, Inches

THEMES = {
    "default": {
        "name": "Default",
        "bg": RGBColor(255, 255, 255),
        "fg": RGBColor(25, 28, 33),
        "accent": RGBColor(35, 99, 188),
        "secondary": RGBColor(243, 246, 249),
        "font_family": "Inter",
        "title_size": Pt(40),
        "subtitle_size": Pt(20),
        "h2_size": Pt(28),
        "body_size": Pt(18),
        "padding": Inches(0.6),
        "footer_size": Pt(10),
    },
    "dark": {
        "name": "Dark",
        "bg": RGBColor(18, 20, 24),
        "fg": RGBColor(235, 238, 243),
        "accent": RGBColor(93, 156, 236),
        "secondary": RGBColor(34, 38, 44),
        "font_family": "Inter",
        "title_size": Pt(40),
        "subtitle_size": Pt(20),
        "h2_size": Pt(28),
        "body_size": Pt(18),
        "padding": Inches(0.6),
        "footer_size": Pt(10),
    },
}

def get_theme(template_id: str | None, style: dict | None = None) -> dict:
    base = THEMES.get((template_id or "default"), THEMES["default"]).copy()
    # style kann einzelne Felder überschreiben (Farben in #RRGGBB oder pptx RGBColor)
    if style:
        for k, v in style.items():
            if isinstance(v, str) and v.startswith("#") and len(v) == 7:
                base[k] = _hex_to_rgb(v)
            else:
                base[k] = v
    return base

def _hex_to_rgb(hex_str: str):
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return RGBColor(r, g, b)

