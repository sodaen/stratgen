# -*- coding: utf-8 -*-
from __future__ import annotations
from io import BytesIO
from typing import Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

def _pick_font(family: str | None, px: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    fam = (family or "").strip() or "DejaVuSans"
    try:
        return ImageFont.truetype(f"{fam}.ttf", px)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", px)
        except Exception:
            return ImageFont.load_default()

def _hex_to_rgb(hexstr: str) -> tuple[int,int,int]:
    s = (hexstr or "").strip().lstrip("#")
    if len(s) != 6:
        return (0,0,0)
    return (int(s[0:2],16), int(s[2:4],16), int(s[4:6],16))

def render_title_png(
    title: str,
    subtitle: Optional[str],
    style: Dict[str, object],
    size: Tuple[int,int] = (1280,720),
) -> bytes:
    # Maße & Style robust auswerten
    w, h = max(int(size[0]), 64), max(int(size[1]), 64)
    bg  = _hex_to_rgb(str(style.get("bg_color", "FFFFFF")))
    fg  = _hex_to_rgb(str(style.get("text_color", "000000")))
    accent = _hex_to_rgb(str(style.get("accent_color", "2F5597")))
    tpx = max(int(style.get("title_size", 36)), 10)
    bpx = max(int(style.get("body_size", 18)), 10)
    margin = max(int(style.get("margin", 20)), 0)
    tfont = _pick_font(str(style.get("title_font", "DejaVuSans")), tpx)
    bfont = _pick_font(str(style.get("body_font",  "DejaVuSans")), bpx)

    im = Image.new("RGB", (w,h), color=bg)
    draw = ImageDraw.Draw(im)

    # Akzentlinie oben
    draw.rectangle([0, 0, w, max(4, h//200)], fill=accent)

    # Titel zentrieren
    tb = draw.textbbox((0,0), title or "", font=tfont)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    tx = (w - tw) // 2
    ty = margin + 20
    draw.text((tx, ty), title or "", font=tfont, fill=fg)

    # Untertitel (optional), ebenfalls zentriert
    if subtitle:
        sb = draw.textbbox((0,0), subtitle, font=bfont)
        sw, sh = sb[2]-sb[0], sb[3]-sb[1]
        sx = (w - sw) // 2
        sy = ty + th + max(12, bpx//2)
        draw.text((sx, sy), subtitle, font=bfont, fill=fg)

    bio = BytesIO()
    im.save(bio, format="PNG")
    return bio.getvalue()
