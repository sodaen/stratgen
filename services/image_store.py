
from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Any
import uuid, json, time, shutil, imghdr

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "images" / "library"
INDEX = ROOT / "images" / "index.json"

class ImageItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    path: str
    url: Optional[str] = None
    tags: list[str] = []
    customer: Optional[str] = None
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    created_at: float = Field(default_factory=lambda: time.time())
    meta: dict[str, Any] = {}

def _load() -> list[ImageItem]:
    if not INDEX.exists():
        return []
    try:
        data = json.loads(INDEX.read_text(encoding="utf-8"))
        return [ImageItem(**x) for x in data]
    except Exception:
        return []

def _save(items: list[ImageItem]):
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps([i.model_dump() for i in items], ensure_ascii=False, indent=2), encoding="utf-8")

def list_images(filters: dict[str,str] | None=None) -> list[dict[str,Any]]:
    items = _load()
    if filters:
        def ok(it: ImageItem) -> bool:
            for k,v in filters.items():
                if not v: 
                    continue
                if k in ("tag","tags"):
                    if v not in it.tags: 
                        return False
                elif getattr(it,k,None) != v:
                    return False
            return True
        items=[i for i in items if ok(i)]
    return [i.model_dump() for i in items]

def add_image_file(src_path: Path, customer: Optional[str], tags: list[str], topic: Optional[str], subtopic: Optional[str]) -> ImageItem:
    LIB.mkdir(parents=True, exist_ok=True)
    suffix = src_path.suffix.lower() or ".png"
    dest = LIB / f"{uuid.uuid4()}{suffix}"
    shutil.copy2(src_path, dest)
    item = ImageItem(
        path=str(dest.relative_to(ROOT)),
        customer=customer,
        tags=tags,
        topic=topic,
        subtopic=subtopic,
        meta={"format": imghdr.what(dest) or suffix.strip(".")}
    )
    items = _load(); items.append(item); _save(items)
    return item

def remove_image(id: str) -> bool:
    items = _load()
    left=[]; deleted=False; del_path=None
    for it in items:
        if it.id == id:
            deleted=True; del_path = ROOT / it.path
        else:
            left.append(it)
    if deleted:
        if del_path and del_path.exists():
            try: del_path.unlink()
            except Exception: pass
        _save(left)
    return deleted

def resolve_for_slide(customer: str, topic: str, subtopic: str, tokens: list[str]) -> Optional[Path]:
    items = _load()
    norm_tokens=[t.strip().lower() for t in tokens if t and isinstance(t,str)]
    def score(it: ImageItem)->int:
        s=0
        if it.customer and customer and it.customer==customer: s+=4
        if it.topic==topic and (it.subtopic or "")==(subtopic or ""): s+=3
        elif it.topic==topic: s+=2
        tagset=[x.lower() for x in it.tags]
        s+=sum(1 for t in norm_tokens if t in tagset)
        return s
    items_sorted=sorted(items, key=lambda it:(score(it), it.created_at), reverse=True)
    for it in items_sorted:
        if score(it)>0:
            p = ROOT / it.path
            if p.exists(): return p
    # Fallback: irgendein Bild
    for it in items_sorted:
        p=ROOT / it.path
        if p.exists(): return p
    return None

def resolve_by_id(img_id: str) -> Optional[Path]:
    for it in _load():
        if it.id == img_id:
            p = ROOT / it.path
            return p if p.exists() else None
    return None
