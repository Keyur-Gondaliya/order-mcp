from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.context import current_business_id
from app.services.orders import (
    cancel_order,
    create_order,
    get_order,
    refund_order,
    search_orders,
    update_order_status,
)

mcp = FastMCP("order-system")

# Set once at startup for stdio mode (where there's no HTTP context).
# Ignored when running via HTTP transport — contextvar takes precedence.
_stdio_business_id: int | None = None


def set_stdio_business_id(business_id: int) -> None:
    global _stdio_business_id
    _stdio_business_id = business_id


def _get_business_id() -> int:
    biz_id = current_business_id.get()
    if biz_id is not None:
        return biz_id
    if _stdio_business_id is not None:
        return _stdio_business_id
    raise ValueError(
        "No business context. "
        "For stdio mode, set the MCP_BUSINESS_TOKEN environment variable."
    )


@mcp.tool()
def search_orders_tool(
    customer: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search orders for the authenticated business. Filter by customer email and/or status.

    Args:
        customer: Customer email to filter by (exact match, case-insensitive).
        status: One of pending, paid, shipped, delivered, cancelled, refunded.
        limit: Max results to return (default 20).
    """
    return search_orders(business_id=_get_business_id(), customer=customer, status=status, limit=limit)


@mcp.tool()
def get_order_tool(order_id: str) -> dict:
    """Look up a single order by its ID (e.g. 'ORD-1001').

    Args:
        order_id: The order's unique identifier.
    """
    return get_order(order_id=order_id, business_id=_get_business_id())


@mcp.tool()
def create_order_tool(customer: str, items: list[dict]) -> dict:
    """Create a new order for the authenticated business. Starts in 'pending' status.

    Args:
        customer: Customer email.
        items: List of line items — each needs sku (str), qty (int), price (float).
    """
    return create_order(business_id=_get_business_id(), customer=customer, items=items)


@mcp.tool()
def update_order_status_tool(order_id: str, status: str) -> dict:
    """Update the status of an existing order.

    Args:
        order_id: The order to update.
        status: One of pending, paid, shipped, delivered, cancelled, refunded.
    """
    return update_order_status(order_id=order_id, business_id=_get_business_id(), status=status)


@mcp.tool()
def cancel_order_tool(order_id: str, reason: str = "") -> dict:
    """Cancel a pending or paid order.

    Args:
        order_id: The order to cancel.
        reason: Optional reason.
    """
    return cancel_order(order_id=order_id, business_id=_get_business_id(), reason=reason)


@mcp.tool()
def refund_order_tool(order_id: str, reason: str = "") -> dict:
    """Refund a shipped, delivered, or paid order.

    Args:
        order_id: The order to refund.
        reason: Optional reason.
    """
    return refund_order(order_id=order_id, business_id=_get_business_id(), reason=reason)
