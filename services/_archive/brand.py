from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional
import json, re, uuid

BRAND_DIR = Path("data/brands"); BRAND_DIR.mkdir(parents=True, exist_ok=True)

def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or uuid.uuid4().hex[:8]

def _hex_to_rgb(hex_str: str | None):
    if not hex_str: return None
    h = hex_str.strip().lstrip("#")
    if len(h) in (3,4):
        h = "".join(c*2 for c in h[:3])
    if len(h) != 6: return None
    try:
        return tuple(int(h[i:i+2], 16) for i in (0,2,4))
    except Exception:
        return None

def save_brand(customer_name: str, primary: str | None, secondary: str | None, accent: str | None, logo_bytes: bytes | None, logo_ext: str = "png") -> Dict[str, Any]:
    slug = _slug(customer_name)
    root = BRAND_DIR / slug
    root.mkdir(parents=True, exist_ok=True)
    logo_path = None
    if logo_bytes:
        logo_path = root / f"logo.{logo_ext or 'png'}"
        with open(logo_path, "wb") as f:
            f.write(logo_bytes)
        logo_path = logo_path.resolve().as_posix()
    meta = {
        "id": slug,
        "name": customer_name,
        "colors": {
            "primary": primary,
            "secondary": secondary,
            "accent": accent
        },
        "logo_path": logo_path
    }
    (root / "brand.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta

def get_brand(brand_id: str) -> Optional[Dict[str, Any]]:
    p = BRAND_DIR / brand_id / "brand.json"
    if not p.exists():
        return None
    meta = json.loads(p.read_text(encoding="utf-8"))
    # angereicherte RGBs
    c = meta.get("colors") or {}
    meta["rgb"] = {
        "primary": _hex_to_rgb(c.get("primary")),
        "secondary": _hex_to_rgb(c.get("secondary")),
        "accent": _hex_to_rgb(c.get("accent")),
    }
    return meta

def list_brands() -> Dict[str, Any]:
    out = []
    for d in BRAND_DIR.iterdir():
        if (d / "brand.json").exists():
            out.append(json.loads((d / "brand.json").read_text(encoding="utf-8")))
    return {"items": out}
