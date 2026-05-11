# Order MCP Server

A lightweight **Model Context Protocol (MCP)** server that exposes order-management tools to any MCP-compatible client (Claude Code, Claude Desktop, etc.).

Backed by an **in-memory mock store** so it runs out of the box — swap in a real database or REST client when you're ready.

---

## Features

| Tool | Description |
|------|-------------|
| `search_orders` | List orders, optionally filtered by customer email and/or status |
| `get_order` | Fetch a single order by ID |
| `create_order` | Create a new order (starts as `pending`) |
| `update_order_status` | Move an order through the status lifecycle |
| `cancel_order` | Cancel a `pending` or `paid` order |
| `refund_order` | Refund a `shipped`, `delivered`, or `paid` order |

---

## Order Data Model

```json
{
  "id":         "ORD-1001",
  "customer":   "alice@example.com",
  "items": [
    { "sku": "BOOK-42", "qty": 1, "price": 19.99 }
  ],
  "total":      19.99,
  "status":     "shipped",
  "created_at": "2026-05-11T19:48:26.294620+00:00",
  "updated_at": "2026-05-11T19:48:26.294620+00:00"
}
```

**Valid statuses:** `pending` → `paid` → `shipped` → `delivered` → `cancelled` / `refunded`

---

## Requirements

- Python 3.10+
- [`mcp`](https://pypi.org/project/mcp/) SDK

---

## Installation

```bash
# 1. Clone the repo
git clone git@github.com:Keyur-Gondaliya/order-mcp.git
cd order-mcp

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Server

```bash
python order_server.py
```

The server communicates over **stdio** — the standard transport for local MCP clients. You won't see output in the terminal; connect via a client instead.

---

## Connecting to Claude Code

Add the server to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "order-system": {
      "command": "/path/to/order-mcp/.venv/bin/python",
      "args": ["/path/to/order-mcp/order_server.py"]
    }
  }
}
```

Replace `/path/to/order-mcp` with the actual path on your machine.

### Connecting to Claude Desktop

Add the same block under `mcpServers` in your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

---

## Seeded Demo Data

The server starts with three demo orders so tools work immediately:

| ID | Customer | Items | Total | Status |
|----|----------|-------|-------|--------|
| ORD-1001 | alice@example.com | 1× BOOK-42 | $19.99 | shipped |
| ORD-1002 | bob@example.com | 2× MUG-RED | $19.00 | pending |
| ORD-1003 | alice@example.com | 3× PEN-BLK, 1× PAD-A5 | $10.50 | paid |

> **Note:** The store is in-memory only — data resets every time the server restarts.

---

## Extending the Server

To connect a real backend, replace the `OrderStore` methods in `order_server.py`:

```python
class OrderStore:
    def get(self, order_id: str) -> dict | None: ...
    def search(self, customer, status, limit) -> list[dict]: ...
    def create(self, customer, items) -> dict: ...
    def update_status(self, order_id, status) -> dict | None: ...
```

The MCP tool layer above is unchanged — only the data layer needs swapping.

---

## License

MIT
