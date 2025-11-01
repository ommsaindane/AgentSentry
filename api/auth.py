from typing import Optional
from fastapi import Header, HTTPException
from api.settings import settings

def require_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    Simple API key check. If AGENTSENTRY_API_KEY is unset, allow all (dev mode).
    Otherwise expect header: Authorization: Bearer <key>
    """
    expected = getattr(settings, "api_key", None)
    if not expected:
        return  # dev mode
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid authorization header")
    token = authorization[len("Bearer "):].strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="forbidden")
