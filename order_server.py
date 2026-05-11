"""
Order System MCP Server
=======================
A local MCP server (stdio transport) that exposes order-management tools
to any MCP-compatible client (Claude Desktop, Claude Code, etc).

Backed by an in-memory mock store so you can run it standalone.
Replace the OrderStore methods with real DB / REST calls when ready.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Mock data layer
# ---------------------------------------------------------------------------
# In a real server this would be a DB connection or an HTTP client.
# Kept as a small class so it's obvious where to swap in real I/O.

OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]
VALID_STATUSES: set[str] = {
    "pending", "paid", "shipped", "delivered", "cancelled", "refunded"
}


class OrderStore:
    """In-memory order store. Swap for a real backend later."""

    def __init__(self) -> None:
        self._orders: dict[str, dict] = {}
        self._seed()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _seed(self) -> None:
        # A handful of demo rows so search/get work out of the box.
        demo = [
            {
                "id": "ORD-1001",
                "customer": "alice@example.com",
                "items": [{"sku": "BOOK-42", "qty": 1, "price": 19.99}],
                "total": 19.99,
                "status": "shipped",
            },
            {
                "id": "ORD-1002",
                "customer": "bob@example.com",
                "items": [{"sku": "MUG-RED", "qty": 2, "price": 9.50}],
                "total": 19.00,
                "status": "pending",
            },
            {
                "id": "ORD-1003",
                "customer": "alice@example.com",
                "items": [
                    {"sku": "PEN-BLK", "qty": 3, "price": 2.00},
                    {"sku": "PAD-A5",  "qty": 1, "price": 4.50},
                ],
                "total": 10.50,
                "status": "paid",
            },
        ]
        for o in demo:
            o["created_at"] = self._now()
            o["updated_at"] = o["created_at"]
            self._orders[o["id"]] = o

    # ---- read --------------------------------------------------------------
    def get(self, order_id: str) -> dict | None:
        return self._orders.get(order_id)

    def search(
        self,
        customer: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        results = list(self._orders.values())
        if customer:
            results = [o for o in results if o["customer"].lower() == customer.lower()]
        if status:
            results = [o for o in results if o["status"] == status]
        # newest first
        results.sort(key=lambda o: o["created_at"], reverse=True)
        return results[:limit]

    # ---- write -------------------------------------------------------------
    def create(self, customer: str, items: list[dict]) -> dict:
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        total = round(sum(i["qty"] * i["price"] for i in items), 2)
        order = {
            "id": order_id,
            "customer": customer,
            "items": items,
            "total": total,
            "status": "pending",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self._orders[order_id] = order
        return order

    def update_status(self, order_id: str, status: str) -> dict | None:
        order = self._orders.get(order_id)
        if not order:
            return None
        order["status"] = status
        order["updated_at"] = self._now()
        return order


store = OrderStore()


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
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}"
        )
    return store.search(customer=customer, status=status, limit=limit)


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
    order = store.get(order_id)
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
    return store.create(customer=customer, items=items)


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
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}"
        )
    order = store.update_status(order_id, status)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return order


@mcp.tool()
def cancel_order(order_id: str, reason: str = "") -> dict:
    """Cancel an order. Only orders in 'pending' or 'paid' can be cancelled;
    'shipped' or 'delivered' orders should be refunded instead.

    Args:
        order_id: The order to cancel.
        reason: Optional human-readable reason (stored on the order).

    Returns:
        The cancelled order.
    """
    order = store.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    if order["status"] not in {"pending", "paid"}:
        raise ValueError(
            f"Cannot cancel order in status '{order['status']}'. "
            f"Use refund_order for shipped/delivered orders."
        )
    updated = store.update_status(order_id, "cancelled")
    if reason:
        updated["cancel_reason"] = reason
    return updated


@mcp.tool()
def refund_order(order_id: str, reason: str = "") -> dict:
    """Refund a shipped or delivered order.

    Args:
        order_id: The order to refund.
        reason: Optional human-readable reason.

    Returns:
        The refunded order.
    """
    order = store.get(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    if order["status"] not in {"shipped", "delivered", "paid"}:
        raise ValueError(
            f"Cannot refund order in status '{order['status']}'."
        )
    updated = store.update_status(order_id, "refunded")
    if reason:
        updated["refund_reason"] = reason
    return updated


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# stdio is the right transport for local clients like Claude Desktop.
# Switch to "streamable-http" if you ever want to expose this remotely.
if __name__ == "__main__":
    mcp.run(transport="stdio")
