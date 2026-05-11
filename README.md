# Order MCP Server

A lightweight **Model Context Protocol (MCP)** server that exposes order-management tools to any MCP-compatible client (Claude Code, Claude Desktop, etc.).

Backed by **PostgreSQL** via Docker Compose — data persists across restarts.

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

## Database Schema

```
orders
├── id            VARCHAR(50)   PRIMARY KEY
├── customer      VARCHAR(255)  NOT NULL
├── total         NUMERIC(10,2)
├── status        VARCHAR(20)   DEFAULT 'pending'
├── cancel_reason TEXT
├── refund_reason TEXT
├── created_at    TIMESTAMPTZ
└── updated_at    TIMESTAMPTZ

order_items
├── id        SERIAL        PRIMARY KEY
├── order_id  VARCHAR(50)   FK → orders.id
├── sku       VARCHAR(100)
├── qty       INTEGER
└── price     NUMERIC(10,2)
```

---

## Requirements

- Python 3.10+
- Docker & Docker Compose
- [`mcp`](https://pypi.org/project/mcp/), `psycopg2-binary`, `python-dotenv`

---

## Installation

```bash
# 1. Clone the repo
git clone git@github.com:Keyur-Gondaliya/order-mcp.git
cd order-mcp

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment (defaults work with docker-compose)
cp .env.example .env
```

---

## Starting the Database

```bash
docker compose up -d
```

This starts a PostgreSQL 16 container on port **5432** with a persistent volume.
The schema and demo seed data are applied automatically on first start via `init.sql`.

To stop and remove containers (data volume is preserved):

```bash
docker compose down
```

To wipe all data and start fresh:

```bash
docker compose down -v
```

---

## Running the Server

```bash
python order_server.py
```

On startup the server:
1. Connects to PostgreSQL using values from `.env` (defaults: `localhost:5432`, db/user/pass all `orders`)
2. Creates tables if they don't exist
3. Seeds demo data if the `orders` table is empty
4. Starts listening on **stdio** for MCP clients

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

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `orders` | Database name |
| `DB_USER` | `orders` | Database user |
| `DB_PASSWORD` | `orders` | Database password |

Copy `.env.example` to `.env` and adjust for your environment.

---

## Seeded Demo Data

Three demo orders are inserted on first startup:

| ID | Customer | Items | Total | Status |
|----|----------|-------|-------|--------|
| ORD-1001 | alice@example.com | 1× BOOK-42 | $19.99 | shipped |
| ORD-1002 | bob@example.com | 2× MUG-RED | $19.00 | pending |
| ORD-1003 | alice@example.com | 3× PEN-BLK, 1× PAD-A5 | $10.50 | paid |

---

## License

MIT
