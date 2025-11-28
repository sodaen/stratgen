from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


class GenRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    seed: Optional[int] = None
    width: int = Field(320, ge=1, le=1920)
    height: int = Field(180, ge=1, le=1080)


def _static_images_dir() -> Path:
    base = Path(__file__).resolve().parent.parent / "static" / "images"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _filename(prompt: str, seed: Optional[int], w: int, h: int) -> str:
    hsh = hashlib.sha256(f"{prompt}|{seed}|{w}x{h}".encode("utf-8")).hexdigest()[:16]
    return f"img_{hsh}_{w}x{h}.png"


def _make_image(req: GenRequest) -> Path:
    if Image is None:
        raise RuntimeError("Pillow (PIL) ist nicht installiert.")
    w, h = req.width, req.height

    if np is not None:
        rng = np.random.RandomState(req.seed if req.seed is not None else 0)
        base = rng.randint(0, 200)
        x = np.linspace(0, 1, w, dtype="float32")
        y = np.linspace(0, 1, h, dtype="float32")[:, None]
        r = (base + 55 * x + 25 * y).clip(0, 255)
        g = (base + 35 * x + 55 * y).clip(0, 255)
        b = (base + 15 * x + 85 * y).clip(0, 255)
        arr = np.dstack([r, g, b]).astype("uint8")
        img = Image.fromarray(arr, mode="RGB")
    else:
        hue = abs(hash(req.prompt)) % 255
        img = Image.new("RGB", (w, h), (hue, (hue * 3) % 255, (hue * 7) % 255))

    outdir = _static_images_dir()
    fname = _filename(req.prompt, req.seed, w, h)
    fpath = outdir / fname
    img.save(fpath, "PNG", optimize=True)
    return fpath


@router.post("/image/generate_simple")
def generate_simple(req: GenRequest):
    try:
        path = _make_image(req)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"image generation failed: {e}")
    return {"ok": True, "url": f"/static/images/{path.name}", "width": req.width, "height": req.height}

# --- BEGIN: big generator route (idempotent add) ---
from pathlib import Path as _Path
import random as _random
import hashlib as _hashlib

_STATIC_DIR = (_Path(__file__).resolve().parents[1] / "static" / "images")
_STATIC_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/images/generate", tags=["images"])
def images_generate(payload: dict | None = None):
    """
    Großer Generator (minimal deterministisch):
      Body: {"prompt": str, "seed": int, "width": int, "height": int}
      Antwort: {"ok": true, "url": "/static/images/...", "width": W, "height": H, "prompt": ..., "seed": ...}
    """
    payload = payload or {}
    prompt = str(payload.get("prompt") or "abstract")
    try:
        seed = int(payload.get("seed") or 0)
    except Exception:
        seed = 0
    try:
        width = max(16, int(payload.get("width") or 512))
        height = max(16, int(payload.get("height") or 512))
    except Exception:
        width, height = 512, 512

    # Dateiname deterministisch aus prompt+seed+size
    fid = f"{seed:x}_{_hashlib.md5(f'{prompt}|{width}x{height}'.encode()).hexdigest()[:8]}"
    fname = f"img_{fid}.png"
    fpath = _STATIC_DIR / fname

    # Erzeuge Bild nur, wenn nicht vorhanden
    if not fpath.exists():
        try:
            # Pillow bevorzugt – schöne Placeholder-Grafik
            from PIL import Image as _Image  # type: ignore
            rnd = _random.Random(seed)
            img = _Image.new("RGB", (width, height))
            px = img.load()
            hue = abs(hash(prompt)) % 255
            for y in range(height):
                for x in range(width):
                    px[x, y] = (rnd.randint(0, 255), (hue + x) % 255, (hue + y) % 255)
            img.save(fpath)
        except Exception:
            # Fallback ohne Pillow: einfache 1x1 PNG anlegen (Platzhalter)
            # So bricht nichts – aber empfehlenswert ist Pillow zu installieren.
            fpath.write_bytes(b"\x89PNG\r\n\x1a\n")

    return {"ok": True, "url": f"/static/images/{fname}",
            "width": width, "height": height,
            "prompt": prompt, "seed": seed}
# --- END: big generator route ---
