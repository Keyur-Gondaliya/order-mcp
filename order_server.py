"""
Order System MCP Server
=======================
MCP server (stdio transport) exposing order-management tools.
Backed by PostgreSQL — configure via environment variables or a .env file
(copy .env.example → .env and adjust values).

Start the database first:
    docker compose up -d

Then run the server:
    python order_server.py
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import Literal

import psycopg2
import psycopg2.extras
import psycopg2.pool
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]
VALID_STATUSES: set[str] = {
    "pending", "paid", "shipped", "delivered", "cancelled", "refunded"
}

# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1,
            10,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "orders"),
            user=os.getenv("DB_USER", "orders"),
            password=os.getenv("DB_PASSWORD", "orders"),
        )
    return _pool


@contextmanager
def _cursor():
    """Yield a RealDictCursor. Commits on success, rolls back on error."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

def _init_db() -> None:
    """Create tables and seed demo rows if the DB is empty."""
    with _cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id            VARCHAR(50)   PRIMARY KEY,
                customer      VARCHAR(255)  NOT NULL,
                total         NUMERIC(10,2) NOT NULL,
                status        VARCHAR(20)   NOT NULL DEFAULT 'pending',
                cancel_reason TEXT,
                refund_reason TEXT,
                created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id        SERIAL        PRIMARY KEY,
                order_id  VARCHAR(50)   NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                sku       VARCHAR(100)  NOT NULL,
                qty       INTEGER       NOT NULL CHECK (qty > 0),
                price     NUMERIC(10,2) NOT NULL CHECK (price >= 0)
            )
        """)
        cur.execute("SELECT COUNT(*) AS cnt FROM orders")
        if cur.fetchone()["cnt"] == 0:
            psycopg2.extras.execute_values(cur, """
                INSERT INTO orders (id, customer, total, status) VALUES %s
            """, [
                ("ORD-1001", "alice@example.com", 19.99, "shipped"),
                ("ORD-1002", "bob@example.com",   19.00, "pending"),
                ("ORD-1003", "alice@example.com", 10.50, "paid"),
            ])
            psycopg2.extras.execute_values(cur, """
                INSERT INTO order_items (order_id, sku, qty, price) VALUES %s
            """, [
                ("ORD-1001", "BOOK-42", 1, 19.99),
                ("ORD-1002", "MUG-RED", 2,  9.50),
                ("ORD-1003", "PEN-BLK", 3,  2.00),
                ("ORD-1003", "PAD-A5",  1,  4.50),
            ])


# ---------------------------------------------------------------------------
# Row → dict helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("order-system")


@mcp.tool()
def search_orders(
    customer: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search orders. Filter by customer email and/or status.

    Args:
        customer: Customer email to filter by (exact match, case-insensitive).
        status: One of pending, paid, shipped, delivered, cancelled, refunded.
        limit: Max results to return (default 20).

    Returns:
        A list of matching order objects, newest first.
    """
    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}")

    with _cursor() as cur:
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


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Look up a single order by its ID (e.g. 'ORD-1001').

    Args:
        order_id: The order's unique identifier.

    Returns:
        The full order object.

    Raises:
        ValueError: if no order with that ID exists.
    """
    with _cursor() as cur:
        order = _load_order(cur, order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return order


@mcp.tool()
def create_order(customer: str, items: list[dict]) -> dict:
    """Create a new order. Newly created orders start in 'pending' status.

    Args:
        customer: Customer email.
        items: List of line items. Each item must have keys:
               sku (str), qty (int > 0), price (float >= 0).

    Returns:
        The created order, including its assigned ID and computed total.
    """
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

    with _cursor() as cur:
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


@mcp.tool()
def update_order_status(order_id: str, status: str) -> dict:
    """Update the status of an existing order.

    Args:
        order_id: The order to update.
        status: New status. One of pending, paid, shipped, delivered,
                cancelled, refunded.

    Returns:
        The updated order.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}")

    with _cursor() as cur:
        cur.execute(
            "UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s RETURNING id",
            (status, order_id),
        )
        if not cur.fetchone():
            raise ValueError(f"Order '{order_id}' not found.")
        return _load_order(cur, order_id)


@mcp.tool()
def cancel_order(order_id: str, reason: str = "") -> dict:
    """Cancel an order. Only orders in 'pending' or 'paid' can be cancelled;
    'shipped' or 'delivered' orders should be refunded instead.

    Args:
        order_id: The order to cancel.
        reason: Optional human-readable reason.

    Returns:
        The cancelled order.
    """
    with _cursor() as cur:
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
            """
            UPDATE orders
               SET status = 'cancelled', cancel_reason = %s, updated_at = NOW()
             WHERE id = %s
            """,
            (reason or None, order_id),
        )
        return _load_order(cur, order_id)


@mcp.tool()
def refund_order(order_id: str, reason: str = "") -> dict:
    """Refund a shipped or delivered order.

    Args:
        order_id: The order to refund.
        reason: Optional human-readable reason.

    Returns:
        The refunded order.
    """
    with _cursor() as cur:
        cur.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Order '{order_id}' not found.")
        if row["status"] not in {"shipped", "delivered", "paid"}:
            raise ValueError(f"Cannot refund order in status '{row['status']}'.")
        cur.execute(
            """
            UPDATE orders
               SET status = 'refunded', refund_reason = %s, updated_at = NOW()
             WHERE id = %s
            """,
            (reason or None, order_id),
        )
        return _load_order(cur, order_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _init_db()
    mcp.run(transport="stdio")
