
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.brand_store import load_brand, save_brand
from services.validators import validate_colors  # existiert bereits

router = APIRouter(prefix="/brand", tags=["brand"])

class BrandSetReq(BaseModel):
    customer_name: str
    primary: str
    secondary: str
    accent: str
    logo_path: Optional[str] = ""

@router.post("/set")
def set_brand(req: BrandSetReq):
    # Farben validieren (wir akzeptieren #RRGGBB oder RGB-ähnlich, falls dein Validator das kann)
    validate_colors(req.primary, req.secondary, req.accent)
    save_brand(req.customer_name, {
        "primary": req.primary,
        "secondary": req.secondary,
        "accent": req.accent,
        "logo_path": req.logo_path or ""
    })
    return {"ok": True}

@router.get("/get")
def get_brand(customer_name: str):
    data = load_brand(customer_name)
    if not data:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True, "profile": data}
