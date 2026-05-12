from __future__ import annotations

from fastapi import Header, HTTPException

from app.services import tokens as token_svc


def get_current_business(authorization: str = Header(...)) -> int:
    """FastAPI dependency — validates Bearer token and returns business_id."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must be 'Bearer <token>'")
    token = authorization[7:].strip()
    business_id = token_svc.validate_token(token)
    if business_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return business_id
