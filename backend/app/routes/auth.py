from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_business
from app.schemas import LoginRequest, RegisterRequest
from app.services import businesses as biz_svc
from app.services import tokens as token_svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    try:
        return biz_svc.register_business(name=body.name, password=body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(body: LoginRequest):
    try:
        return biz_svc.login_business(name=body.name, password=body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/token")
def get_token(business_id: int = Depends(get_current_business)):
    token = token_svc.get_token(business_id)
    business = biz_svc.get_business_by_id(business_id)
    return {"token": token, "business": business}


@router.post("/token/regenerate")
def regenerate_token(business_id: int = Depends(get_current_business)):
    token = token_svc.rotate_token(business_id)
    return {"token": token}


@router.delete("/token", status_code=204)
def revoke_token(business_id: int = Depends(get_current_business)):
    token_svc.revoke_token(business_id)
