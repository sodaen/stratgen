from __future__ import annotations
import os, re, base64, uuid
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

EXPORT_DIR = Path("data/exports/images")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

IMG_TOKEN = re.compile(r"#IMG\\(([^\\)]*)\\)", re.I)

def parse_img_tokens(bullets: List[str]) -> Dict[str, Any]:
    """
    Erkennt #IMG(...) in Bullets.
    Syntax: #IMG(keyword[, style=icon|photo][, size=sm|md|lg])
    Entfernt die Token-Zeilen aus Bullets und gibt geparste Specs zurück.
    """
    images = []
    clean = []
    for b in bullets:
        m = IMG_TOKEN.search(b)
        if not m:
            clean.append(b)
            continue
        inside = m.group(1).strip()
        # Split by comma, parse key=val
        parts = [p.strip() for p in inside.split(",") if p.strip()]
        keyword = parts[0] if parts else "Idea"
        style = "photo"; size = "md"
        for p in parts[1:]:
            if "=" in p:
                k,v = [x.strip().lower() for x in p.split("=",1)]
                if k=="style" and v in ("icon","photo"): style = v
                if k=="size" and v in ("sm","md","lg"): size = v
        images.append({"keyword": keyword, "style": style, "size": size})
    return {"bullets_clean": clean, "images": images}

def _placeholder_png(text: str, size: str="md") -> str:
    # einfache Platzhalter-Grafik
    w,h = {"sm":(800,500), "md":(1100,700), "lg":(1400,900)}.get(size, (1100,700))
    img = Image.new("RGB", (w,h), (242,243,245))
    draw = ImageDraw.Draw(img)
    # einfache Umrandung
    draw.rectangle((10,10,w-10,h-10), outline=(180,180,180), width=3)
    # Text
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()
    text = f"IMG: {text}"
    tw, th = draw.textbbox((0,0), text, font=font)[2:]
    draw.text(((w-tw)//2,(h-th)//2), text, fill=(60,60,60), font=font)
    out = EXPORT_DIR / f"img_ph_{uuid.uuid4().hex[:8]}.png"
    img.save(out.as_posix(), "PNG")
    return out.as_posix()

def _sd_api_url() -> Optional[str]:
    url = os.getenv("SD_API_URL")
    if url and url.startswith("http"):
        return url.rstrip("/")
    return None

def _sd_txt2img(prompt: str, w: int=896, h: int=560, steps: int=20) -> Optional[str]:
    base = _sd_api_url()
    if not base:
        return None
    try:
        resp = requests.post(f"{base}/sdapi/v1/txt2img", json={
            "prompt": prompt,
            "width": w, "height": h,
            "steps": steps,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras"
        }, timeout=60)
        resp.raise_for_status()
        js = resp.json()
        if not js.get("images"):
            return None
        img_b64 = js["images"][0]
        data = base64.b64decode(img_b64.split(",",1)[-1])
        out = EXPORT_DIR / f"img_sd_{uuid.uuid4().hex[:8]}.png"
        with open(out, "wb") as f:
            f.write(data)
        return out.as_posix()
    except Exception:
        return None

def render_image(keyword: str, style: str="photo", size: str="md") -> str:
    # Prompting-Heuristik
    if style=="icon":
        prompt = f"{keyword}, vector flat icon, simple shapes, high contrast, monochrome on white background"
    else:
        prompt = f"{keyword}, high-quality photo, soft light, detailed, professional stock style"
    dims = {"sm":(768,512),"md":(896,560),"lg":(1152,704)}[size]
    out = _sd_txt2img(prompt, w=dims[0], h=dims[1])
    if out:
        return out
    # Fallback: Placeholder
    return _placeholder_png(f"{keyword} ({style})", size=size)


# ----- lazy imports for Pillow / CairoSVG -----
def _ensure_pillow():
    global Image, ImageOps
    try:
        from PIL import Image, ImageOps  # type: ignore
        return True
    except Exception:
        return False

def _ensure_cairosvg():
    try:
        import cairosvg  # type: ignore
        return True
    except Exception:
        return False
