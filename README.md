# Order MCP Server

A lightweight **Model Context Protocol (MCP)** server that exposes order-management tools to any MCP-compatible client (Claude Code, Claude Desktop, etc.).

Backed by **PostgreSQL** via Docker Compose — data persists across restarts.  
Also ships a **FastAPI REST server** and a **React frontend** for browser-based management.

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
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── main.py             # FastAPI app
│   ├── mcp_server.py           # MCP stdio entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init.sql                # SQL schema for Docker first-run
├── frontend/                   # React + Vite app
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

This starts three services:

| Service | Port | Description |
|---------|------|-------------|
| `db` | 5432 | PostgreSQL 16 — schema and seed data applied on first start |
| `backend` | 8000 | FastAPI REST server + MCP HTTP endpoint |
| `frontend` | 80 | React app served via nginx (proxies `/api` → backend) |

Open **http://localhost** to use the web UI.

To stop containers (data volume preserved):

```bash
docker compose down
```

To wipe all data and start fresh:

```bash
docker compose down -v
```

---

## Running without Docker

Start the database first:

```bash
docker compose up -d db
```

Then run whichever server you need:

```bash
cd backend

# MCP server (stdio transport — for Claude Code / Claude Desktop)
python mcp_server.py

# REST API server (HTTP — for the frontend or direct API calls)
uvicorn app.main:app --reload   # listens on http://localhost:8000
```

---

## REST API

The FastAPI server (`backend/app/main.py`) exposes the same order-management logic over HTTP.

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
| `GET` | `/api/auth/token` | Get current token (auto-creates one if none exists) |
| `POST` | `/api/auth/token/regenerate` | Rotate the token |
| `DELETE` | `/api/auth/token` | Revoke the token |

Interactive docs are available at **http://localhost:8000/docs**.

---

## Frontend

The React app (`frontend/`) provides:

- **Orders tab** — filterable table with create, status update, cancel, and refund actions
- **API Access tab** — view/copy your bearer token, regenerate or revoke it, and get ready-to-paste MCP configuration

Built with React 18 + Vite, served via nginx in Docker.

To run locally for development:

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000` (configured in `vite.config.js`).

---

## Connecting to Claude Code

### Option A — stdio (direct Python process)

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

Replace `/path/to/order-mcp` with the actual path on your machine.

### Option B — HTTP (when the Docker stack is running)

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

Get your token from the **API Access** tab in the web UI or via `GET /api/auth/token`.

### Option C — OAuth (easiest)

```bash
claude mcp add order-system -t http localhost:8000/mcp
```

### Connecting to Claude Desktop

Add the stdio block (Option A) under `mcpServers` in your Claude Desktop config:

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
