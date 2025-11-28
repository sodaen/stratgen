from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from services.style_profiles import list_profiles, get_default_name, set_default_name

router = APIRouter(prefix="/style", tags=["style"])

@router.get("/profiles")
def profiles():
    return {"ok": True, "profiles": list_profiles(), "default": get_default_name()}

@router.post("/set_default")
def set_default(name: str = Body(..., embed=True)):
    try:
        set_default_name(name)
        return {"ok": True, "default": name}
    except KeyError:
        return JSONResponse({"ok": False, "error": f"unknown profile: {name}"}, status_code=400)
