
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from pathlib import Path
from typing import Optional
from services.image_store import add_image_file, list_images, remove_image, resolve_for_slide

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    customer_name: Optional[str] = Form(None),
    tags: Optional[str] = Form(""),
    topic: Optional[str] = Form(None),
    subtopic: Optional[str] = Form(None),
):
    tmp = Path("/tmp")/file.filename
    tmp.write_bytes(file.file.read())
    item = add_image_file(tmp, customer_name, [t.strip() for t in tags.split(",") if t.strip()], topic, subtopic)
    try: tmp.unlink()
    except Exception: pass
    return {"ok": True, "image": item.model_dump()}

@router.get("/list")
def list_images_route(
    customer_name: Optional[str] = None,
    tag: Optional[str] = None,
    topic: Optional[str] = None,
    subtopic: Optional[str] = None
):
    flt={}
    if customer_name: flt["customer"]=customer_name
    if topic: flt["topic"]=topic
    if subtopic: flt["subtopic"]=subtopic
    if tag: flt["tag"]=tag
    return list_images(flt)

@router.delete("/remove")
def remove_image_route(id: str = Query(...)):
    ok = remove_image(id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}

@router.get("/resolve")
def resolve_image(customer_name: str, topic: str, subtopic: str = "", tokens: str = ""):
    tok = [t.strip() for t in tokens.split(",") if t.strip()]
    p = resolve_for_slide(customer_name, topic, subtopic, tok)
    if not p:
        raise HTTPException(status_code=404, detail="no match")
    return {"ok": True, "path": str(p)}
