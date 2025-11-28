from __future__ import annotations
from typing import Any, Dict, List
from io import BytesIO
from PIL import Image, ImageDraw

def render_preview(project: Dict[str, Any], slide_plan: List[Dict[str, Any]], width: int = 800) -> bytes:
    W = max(200, min(int(width or 800), 4000))
    H = int(W * 9 / 16)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    title = ((project or {}).get("outline") or {}).get("title") \
            or (project or {}).get("topic") or "Strategy Deck"
    lines = [title, "— Preview —"]
    for i, s in enumerate(slide_plan[:6], start=1):
        t = s.get("title") or s.get("kind") or "Slide"
        lines.append(f"{i}. {t}")

    y = int(0.12 * H)
    x = int(0.08 * W)
    for t in lines:
        d.text((x, y), str(t), fill="black")
        y += int(0.08 * H)

    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()
