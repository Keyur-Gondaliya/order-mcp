"""
Order System REST API
=====================
FastAPI server that exposes the same order-management logic as the MCP server
over a standard HTTP REST API. Backed by the same PostgreSQL database.

Start the database first:
    docker compose up -d

Then run the API server:
    python api_server.py          # listens on http://localhost:8000
"""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

from order_server import (
    _init_db,
    cancel_order,
    create_order,
    get_order,
    refund_order,
    search_orders,
    update_order_status,
)

app = FastAPI(title="Order System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    sku: str
    qty: int
    price: float


class CreateOrderRequest(BaseModel):
    customer: EmailStr
    items: list[LineItem]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("items must contain at least one line item")
        return v


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


class ReasonRequest(BaseModel):
    reason: str = ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/orders")
def list_orders(
    customer: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        return search_orders(customer=customer, status=status, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/orders/{order_id}")
def retrieve_order(order_id: str):
    try:
        return get_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/orders", status_code=201)
def place_order(body: CreateOrderRequest):
    try:
        items = [item.model_dump() for item in body.items]
        return create_order(customer=str(body.customer), items=items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/orders/{order_id}/status")
def change_status(order_id: str, body: UpdateStatusRequest):
    try:
        return update_order_status(order_id=order_id, status=body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/orders/{order_id}/cancel")
def cancel(order_id: str, body: ReasonRequest = ReasonRequest()):
    try:
        return cancel_order(order_id=order_id, reason=body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/orders/{order_id}/refund")
def refund(order_id: str, body: ReasonRequest = ReasonRequest()):
    try:
        return refund_order(order_id=order_id, reason=body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    _init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
