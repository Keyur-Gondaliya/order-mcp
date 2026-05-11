# Order MCP Server

A **Model Context Protocol (MCP)** server that exposes order-management tools to any MCP-compatible client (Claude Code, Claude Desktop, etc.).

Backed by **PostgreSQL** via Docker Compose — data persists across restarts.
Also ships a **FastAPI REST server** and a **React frontend** for browser-based management.

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_orders_tool` | List orders, optionally filtered by customer email and/or status |
| `get_order_tool` | Fetch a single order by ID |
| `create_order_tool` | Create a new order (starts as `pending`) |
| `update_order_status_tool` | Move an order through the status lifecycle |
| `cancel_order_tool` | Cancel a `pending` or `paid` order |
| `refund_order_tool` | Refund a `shipped`, `delivered`, or `paid` order |

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
├── order_id  VARCHAR(50)   FK → orders.id  (CASCADE DELETE)
├── sku       VARCHAR(100)
├── qty       INTEGER       CHECK (qty > 0)
└── price     NUMERIC(10,2) CHECK (price >= 0)

api_tokens
├── id         SERIAL       PRIMARY KEY
├── token      VARCHAR(64)  UNIQUE NOT NULL
└── created_at TIMESTAMPTZ
```

---

## Project Structure

```
order-mcp/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   ├── connection.py   # connection pool + cursor()
│   │   │   └── init.py         # schema bootstrap + seed data
│   │   ├── services/
│   │   │   ├── orders.py       # order business logic
│   │   │   └── tokens.py       # API token management
│   │   ├── routes/
│   │   │   ├── orders.py       # /api/orders endpoints
│   │   │   └── auth.py         # /api/auth endpoints
│   │   ├── mcp.py              # MCP tool definitions (shared by stdio + HTTP)
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── main.py             # FastAPI app — mounts REST routes + /mcp
│   ├── mcp_server.py           # stdio entry point (Claude Code / Desktop)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init.sql                # SQL schema for Docker first-run
├── frontend/                   # React + Vite app
├── .mcp.json                   # Claude Code MCP config (project-scoped)
├── docker-compose.yml
└── README.md
```

---

## Requirements

- Python 3.13+
- Docker & Docker Compose
- Dependencies (see `backend/requirements.txt`): `mcp`, `psycopg2-binary`, `python-dotenv`, `fastapi`, `uvicorn`, `pydantic[email]`

---

## Installation

```bash
# 1. Clone the repo
git clone git@github.com:Keyur-Gondaliya/order-mcp.git
cd order-mcp

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Configure environment (defaults work with docker-compose)
cp .env.example .env
```

---

## Running with Docker (full stack)

```bash
docker compose up -d
```

| Service | Port | Description |
|---------|------|-------------|
| `db` | 5432 | PostgreSQL 16 — schema and seed data applied on first start |
| `backend` | 8000 | FastAPI REST API + MCP HTTP endpoint at `/mcp` |
| `frontend` | 80 | React app served via nginx (proxies `/api` → backend) |

Open **http://localhost** for the web UI, **http://localhost:8000/docs** for API docs.

```bash
docker compose down      # stop (data preserved)
docker compose down -v   # stop + wipe all data
```

---

## Running without Docker

```bash
# Start DB only
docker compose up -d db

# In one terminal — MCP stdio server (used by Claude Code / Desktop)
cd backend
python mcp_server.py

# In another terminal — REST API + /mcp HTTP endpoint
cd backend
uvicorn app.main:app --reload    # http://localhost:8000
```

---

## REST API

### Orders

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/orders` | List orders (`?customer=`, `?status=`, `?limit=`) |
| `GET` | `/api/orders/{id}` | Get a single order |
| `POST` | `/api/orders` | Create an order |
| `PATCH` | `/api/orders/{id}/status` | Update status |
| `POST` | `/api/orders/{id}/cancel` | Cancel an order |
| `POST` | `/api/orders/{id}/refund` | Refund an order |

### API Token

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/auth/token` | Get current token (auto-creates if none exists) |
| `POST` | `/api/auth/token/regenerate` | Rotate to a new token |
| `DELETE` | `/api/auth/token` | Revoke the token |

Interactive docs: **http://localhost:8000/docs**

---

## Frontend

The React app (`frontend/`) provides:

- **Orders tab** — filterable table with create, status update, cancel, and refund actions
- **API Access tab** — view/copy your bearer token, regenerate or revoke it, and get ready-to-paste MCP configuration

To run locally for development:

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000` (configured in `vite.config.js`).

---

## Connecting to Claude Code (CLI)

The project ships a `.mcp.json` at the root — Claude Code auto-loads it when you run `claude` inside the project folder. No extra setup needed.

To verify tools are loaded:
```bash
claude mcp list
```

To add to a **different project** or globally, use one of the options below.

### Option A — stdio (no Docker required)

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "order-system": {
      "command": "/path/to/order-mcp/.venv/bin/python",
      "args": ["/path/to/order-mcp/backend/mcp_server.py"],
      "cwd": "/path/to/order-mcp/backend"
    }
  }
}
```

### Option B — HTTP (requires Docker stack running)

```json
{
  "mcpServers": {
    "order-system": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

Get your token: `curl http://localhost:8000/api/auth/token`

### Option C — OAuth via CLI

```bash
claude mcp add order-system -t http http://localhost:8000/mcp
```

---

## Connecting to Claude Desktop

**macOS config file:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows config file:** `%APPDATA%\Claude\claude_desktop_config.json`

> **Important:** Use `env.PYTHONPATH` (not `cwd`) — Claude Desktop does not support `cwd` in `mcpServers`.

```json
{
  "mcpServers": {
    "order-system": {
      "command": "/path/to/order-mcp/.venv/bin/python",
      "args": ["/path/to/order-mcp/backend/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/order-mcp/backend"
      }
    }
  }
}
```

Replace `/path/to/order-mcp` with the actual path on your machine, then **fully quit (⌘Q) and reopen** Claude Desktop.

> **Note:** Use `/Applications/Claude.app` — not the Claude web PWA installed via Chrome.

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
