from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas import CreateOrderRequest, ReasonRequest, UpdateStatusRequest
from app.services import orders as order_svc

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("")
def list_orders(
    customer: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        return order_svc.search_orders(customer=customer, status=status, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}")
def retrieve_order(order_id: str):
    try:
        return order_svc.get_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", status_code=201)
def place_order(body: CreateOrderRequest):
    try:
        return order_svc.create_order(
            customer=str(body.customer),
            items=[item.model_dump() for item in body.items],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/status")
def change_status(order_id: str, body: UpdateStatusRequest):
    try:
        return order_svc.update_order_status(order_id=order_id, status=body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/cancel")
def cancel(order_id: str, body: ReasonRequest = ReasonRequest()):
    try:
        return order_svc.cancel_order(order_id=order_id, reason=body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/refund")
def refund(order_id: str, body: ReasonRequest = ReasonRequest()):
    try:
        return order_svc.refund_order(order_id=order_id, reason=body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
