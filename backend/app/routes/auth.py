from __future__ import annotations

from fastapi import APIRouter

from app.services import tokens as token_svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/token")
def get_token():
    return {"token": token_svc.get_or_create_token()}


@router.post("/token/regenerate")
def regenerate_token():
    return {"token": token_svc.rotate_token()}


@router.delete("/token", status_code=204)
def revoke_token():
    token_svc.revoke_token()
