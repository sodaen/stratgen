from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from services.ingest import discover_files, reindex

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.get("/scan")
def scan():
    return JSONResponse({"ok": True, "files": [str(p) for p in discover_files()]})

@router.post("/reindex")
def reindex_api(recreate: bool = Body(False)):
    try:
        rep = reindex(recreate=recreate)
        return JSONResponse({"ok": True, "report": rep})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
