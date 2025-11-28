import os
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(api_key: str | None = Security(_api_key_header)):
    required = os.getenv("API_KEY")
    if not required:
        # Kein Key gefordert (Dev-Mode)
        return True
    if api_key == required:
        return True
    raise HTTPException(status_code=403, detail="Forbidden: invalid or missing API key")
