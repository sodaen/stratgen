from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import JSONResponse
from pathlib import Path
from services.template_tools import MASTER_PATH, validate_master, propose_patch, apply_patch, BACKUP_DIR

router = APIRouter(prefix="/template", tags=["template"])

@router.post("/upload")
async def upload_master(file: UploadFile = File(...)):
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    # Backup falls vorhanden
    if MASTER_PATH.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        import shutil, datetime
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy(MASTER_PATH, BACKUP_DIR / f"upload_backup_{ts}.pptx")
    MASTER_PATH.write_bytes(data)
    return JSONResponse({"ok": True, "saved_as": str(MASTER_PATH), "size": len(data)})

@router.get("/validate")
def validate():
    try:
        report = validate_master()
        return JSONResponse({"ok": True, "report": report})
    except AssertionError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

@router.post("/patch")
def patch(dry_run: bool = Body(True)):
    if dry_run:
        plan = propose_patch()
        return JSONResponse({"ok": True, "dry_run": True, "plan": plan})
    else:
        result = apply_patch()
        # validate after patch
        report = validate_master()
        return JSONResponse({"ok": True, "dry_run": False, "result": result, "report_after": report})
