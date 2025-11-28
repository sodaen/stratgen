import os, hashlib, time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.schemas.exports import ExportItem, LatestExport

router = APIRouter(prefix="/exports", tags=["exports"])

def _exports_dir() -> str:
    return os.getenv("EXPORTS_DIR", os.path.join("data","exports"))

def _iter_exports(root: str) -> List[ExportItem]:
    if not os.path.isdir(root):
        return []
    out: List[ExportItem] = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.startswith("."): 
                continue
            path = os.path.join(dirpath, fn)
            try:
                st = os.stat(path)
            except FileNotFoundError:
                continue
            name = fn
            ext = os.path.splitext(fn)[1].lstrip(".").lower()
            # optional checksum: .sha256 neben der Datei
            chks: Optional[str] = None
            sha_path = path + ".sha256"
            if os.path.exists(sha_path):
                try:
                    with open(sha_path,"r",encoding="utf-8",errors="ignore") as fh:
                        chks = fh.read().strip().split()[0]
                except Exception:
                    chks = None
            # Download-URL (konventionell)
            url = f"/exports/download/{name}"
            out.append(ExportItem(name=name, size=st.st_size, mtime=st.st_mtime, url=url, checksum=chks, ext=ext, path=os.path.relpath(path, root)))
    # neueste zuerst
    out.sort(key=lambda e: e.mtime, reverse=True)
    return out

@router.get("/list", response_model=List[ExportItem])
def list_exports(ext: Optional[str] = Query(default=None, description="Filter by extension, e.g. 'pptx' or 'md'")):
    items = _iter_exports(_exports_dir())
    if ext:
        ext = ext.lower().lstrip(".")
        items = [i for i in items if (i.ext or "") == ext]
    return items

@router.get("/latest", response_model=LatestExport)
def latest_export(ext: Optional[str] = Query(default=None)):
    items = list_exports(ext=ext)
    if not items:
        raise HTTPException(status_code=404, detail="no exports found")
    i = items[0]
    return LatestExport(name=i.name, url=i.url or f"/exports/download/{i.name}", size=i.size, mtime=i.mtime, checksum=i.checksum)
