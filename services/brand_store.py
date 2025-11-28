
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Tuple

DATA_DIR = Path("data/brands")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BRAND: Dict[str, Any] = {
    "primary":   "#0B5FFF",   # Titel
    "secondary": "#111827",   # Untertitel
    "accent":    "#22C55E",   # Akzente
    "logo_path": ""
}

def _norm_hex(h: str) -> str:
    h = (h or "").strip()
    if not h:
        return "#000000"
    if not h.startswith("#"):
        h = "#"+h
    if len(h) == 4:  # z.B. #abc => #aabbcc
        h = "#"+ "".join([c*2 for c in h[1:]])
    return h[:7]

def _hex_to_rgb(h: str) -> Tuple[int,int,int]:
    h = _norm_hex(h)
    try:
        return int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
    except Exception:
        return (0,0,0)

def load_brand(customer_name: str) -> Dict[str, Any]:
    f = DATA_DIR / f"{customer_name}.json"
    if not f.exists():
        return DEFAULT_BRAND.copy()
    try:
        return {**DEFAULT_BRAND, **json.loads(f.read_text(encoding="utf-8"))}
    except Exception:
        return DEFAULT_BRAND.copy()

def save_brand(customer_name: str, profile: Dict[str, Any]) -> None:
    data = {**DEFAULT_BRAND, **profile}
    # normalisieren
    data["primary"]   = _norm_hex(data.get("primary",""))
    data["secondary"] = _norm_hex(data.get("secondary",""))
    data["accent"]    = _norm_hex(data.get("accent",""))
    (DATA_DIR / f"{customer_name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_style_for(customer_name: str) -> Dict[str, Any]:
    b = load_brand(customer_name)
    # auf Renderer-Keys mappen
    style = {
        "color_title_rgb":    _hex_to_rgb(b["primary"]),
        "color_subtitle_rgb": _hex_to_rgb(b["secondary"]),
        "color_body_rgb":     (17,24,39),  # dunkles Grau als Default Body
        "color_accent_rgb":   _hex_to_rgb(b["accent"]),
        "logo_path":          b.get("logo_path",""),
        "font_title":         "Inter",
        "font_body":          "Inter",
        "size_title_pt":      40,
        "size_subtitle_pt":   20,
        "size_body_pt":       18
    }
    return style
