from fastapi import Header, HTTPException, status, Depends
from backend.settings import get_settings

def require_api_key(x_api_key: str | None = Header(default=None)):
    s = get_settings()
    if s.API_KEY and x_api_key != s.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return True
