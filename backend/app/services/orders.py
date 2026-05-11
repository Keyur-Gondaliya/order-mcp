from __future__ import annotations

import uuid
from typing import Literal

import psycopg2.extras

from app.db.connection import cursor

OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]

VALID_STATUSES: set[str] = {
    "pending", "paid", "shipped", "delivered", "cancelled", "refunded"
}


def _load_order(cur: psycopg2.extras.RealDictCursor, order_id: str) -> dict | None:
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    row = cur.fetchone()
    if not row:
        return None

    cur.execute(
        "SELECT sku, qty, price FROM order_items WHERE order_id = %s ORDER BY id",
        (order_id,),
    )
    items = [
        {"sku": r["sku"], "qty": r["qty"], "price": float(r["price"])}
        for r in cur.fetchall()
    ]

    order: dict = {
        "id":         row["id"],
        "customer":   row["customer"],
        "items":      items,
        "total":      float(row["total"]),
        "status":     row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }
    if row["cancel_reason"]:
        order["cancel_reason"] = row["cancel_reason"]
    if row["refund_reason"]:
        order["refund_reason"] = row["refund_reason"]
    return order


def search_orders(
    customer: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}")

    with cursor() as cur:
        conditions, params = [], []
        if customer:
            conditions.append("LOWER(customer) = LOWER(%s)")
            params.append(customer)
        if status:
            conditions.append("status = %s")
            params.append(status)

        sql = "SELECT id FROM orders"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(sql, params)
        ids = [r["id"] for r in cur.fetchall()]
        return [o for oid in ids if (o := _load_order(cur, oid)) is not None]


def get_order(order_id: str) -> dict:
    with cursor() as cur:
        order = _load_order(cur, order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return order


def create_order(customer: str, items: list[dict]) -> dict:
    if not customer or "@" not in customer:
        raise ValueError("'customer' must be a valid email address.")
    if not items:
        raise ValueError("'items' must contain at least one line item.")
    for i, item in enumerate(items):
        for key in ("sku", "qty", "price"):
            if key not in item:
                raise ValueError(f"items[{i}] is missing required key '{key}'.")
        if item["qty"] <= 0:
            raise ValueError(f"items[{i}].qty must be > 0.")
        if item["price"] < 0:
            raise ValueError(f"items[{i}].price must be >= 0.")

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    total = round(sum(i["qty"] * i["price"] for i in items), 2)

    with cursor() as cur:
        cur.execute(
            "INSERT INTO orders (id, customer, total, status) VALUES (%s, %s, %s, 'pending')",
            (order_id, customer, total),
        )
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO order_items (order_id, sku, qty, price) VALUES %s",
            [(order_id, item["sku"], item["qty"], item["price"]) for item in items],
        )
        return _load_order(cur, order_id)


def update_order_status(order_id: str, status: str) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}")

    with cursor() as cur:
        cur.execute(
            "UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s RETURNING id",
            (status, order_id),
        )
        if not cur.fetchone():
            raise ValueError(f"Order '{order_id}' not found.")
        return _load_order(cur, order_id)


def cancel_order(order_id: str, reason: str = "") -> dict:
    with cursor() as cur:
        cur.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Order '{order_id}' not found.")
        if row["status"] not in {"pending", "paid"}:
            raise ValueError(
                f"Cannot cancel order in status '{row['status']}'. "
                "Use refund_order for shipped/delivered orders."
            )
        cur.execute(
            "UPDATE orders SET status = 'cancelled', cancel_reason = %s, updated_at = NOW() WHERE id = %s",
            (reason or None, order_id),
        )
        return _load_order(cur, order_id)


def refund_order(order_id: str, reason: str = "") -> dict:
    with cursor() as cur:
        cur.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Order '{order_id}' not found.")
        if row["status"] not in {"shipped", "delivered", "paid"}:
            raise ValueError(f"Cannot refund order in status '{row['status']}'.")
        cur.execute(
            "UPDATE orders SET status = 'refunded', refund_reason = %s, updated_at = NOW() WHERE id = %s",
            (reason or None, order_id),
        )
        return _load_order(cur, order_id)
