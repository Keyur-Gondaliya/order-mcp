from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]


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


class RegisterRequest(BaseModel):
    name: str
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Business name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    name: str
    password: str
