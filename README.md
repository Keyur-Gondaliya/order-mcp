# Order MCP Server

A **multi-tenant order management system** built on the **Model Context Protocol (MCP)**. Each business registers with a name and password, gets its own API token, and can only access its own orders — via REST API, web UI, or any MCP-compatible client (Claude Code, Claude Desktop, etc.).

Backed by **PostgreSQL** via Docker Compose — data persists across restarts.

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_orders_tool` | List your business's orders, optionally filtered by customer email and/or status |
| `get_order_tool` | Fetch a single order by ID (only if it belongs to your business) |
| `create_order_tool` | Create a new order for your business (starts as `pending`) |
| `update_order_status_tool` | Move an order through the status lifecycle |
| `cancel_order_tool` | Cancel a `pending` or `paid` order |
| `refund_order_tool` | Refund a `shipped`, `delivered`, or `paid` order |

---

## Order Data Model

```json
{
  "id":          "ORD-1001",
  "business_id": 1,
  "customer":    "alice@example.com",
  "items": [
    { "sku": "BOOK-42", "qty": 1, "price": 19.99 }
  ],
  "total":      19.99,
  "status":     "shipped",
  "created_at": "2026-05-12T10:00:00+00:00",
  "updated_at": "2026-05-12T10:00:00+00:00"
}
```

**Valid statuses:** `pending` → `paid` → `shipped` → `delivered` → `cancelled` / `refunded`

---

## Database Schema

```
businesses
├── id            SERIAL        PRIMARY KEY
├── name          VARCHAR(255)  UNIQUE NOT NULL
├── password_hash VARCHAR(255)  NOT NULL
└── created_at    TIMESTAMPTZ

api_tokens
├── id          SERIAL       PRIMARY KEY
├── token       VARCHAR(64)  UNIQUE NOT NULL
├── business_id INTEGER      FK → businesses.id  (CASCADE DELETE)
└── created_at  TIMESTAMPTZ

orders
├── id            VARCHAR(50)   PRIMARY KEY
├── business_id   INTEGER       FK → businesses.id
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
```

---

## Project Structure

```
order-mcp/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   ├── connection.py      # connection pool + cursor()
│   │   │   └── init.py            # schema bootstrap + migrations
│   │   ├── services/
│   │   │   ├── businesses.py      # register / login (bcrypt)
│   │   │   ├── orders.py          # order business logic (scoped by business_id)
│   │   │   └── tokens.py          # validate / rotate / revoke tokens
│   │   ├── routes/
│   │   │   ├── orders.py          # /api/orders endpoints (auth required)
│   │   │   └── auth.py            # /api/auth/register, /login, /token
│   │   ├── context.py             # ContextVar for current business (HTTP mode)
│   │   ├── dependencies.py        # FastAPI get_current_business Depends
│   │   ├── mcp.py                 # MCP tool definitions (shared by stdio + HTTP)
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── main.py                # FastAPI app + MCPAuthMiddleware at /mcp
│   ├── mcp_server.py              # stdio entry point (reads MCP_BUSINESS_TOKEN)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init.sql                   # SQL schema for Docker first-run
├── frontend/                      # React + Vite app
├── .mcp.json                      # Claude Code MCP config (project-scoped)
├── docker-compose.yml
└── README.md
```

---

## Requirements

- Python 3.13+
- Docker & Docker Compose
- Dependencies (`backend/requirements.txt`): `mcp`, `psycopg2-binary`, `python-dotenv`, `fastapi`, `uvicorn`, `pydantic[email]`, `bcrypt`

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
| `db` | 5432 | PostgreSQL 16 |
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

# In one terminal — REST API + /mcp HTTP endpoint
cd backend
uvicorn app.main:app --reload    # http://localhost:8000

# In another terminal (optional) — MCP stdio server
cd backend
MCP_BUSINESS_TOKEN=<your-token> python mcp_server.py
```

---

## Authentication

Every business registers once and gets an API token. All API and MCP calls require that token.

### Register a new business

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "password": "secret123"}'
```

```json
{
  "token": "2c41f119fa85b0fd3ed6d04e9c4208e5de277f7937df2460",
  "business": { "id": 1, "name": "Acme Corp", "created_at": "..." }
}
```

### Log in (get token)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "password": "secret123"}'
```

### Verify / refresh token

```bash
curl http://localhost:8000/api/auth/token \
  -H "Authorization: Bearer <your-token>"
```

---

## REST API

All `/api/orders` endpoints require `Authorization: Bearer <your-token>`.

### Orders

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/orders` | List your orders (`?customer=`, `?status=`, `?limit=`) |
| `GET` | `/api/orders/{id}` | Get a single order |
| `POST` | `/api/orders` | Create an order |
| `PATCH` | `/api/orders/{id}/status` | Update status |
| `POST` | `/api/orders/{id}/cancel` | Cancel an order |
| `POST` | `/api/orders/{id}/refund` | Refund an order |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Register a new business — returns `{token, business}` |
| `POST` | `/api/auth/login` | Log in — returns `{token, business}` |
| `GET` | `/api/auth/token` | Verify token + get business info (auth required) |
| `POST` | `/api/auth/token/regenerate` | Rotate to a new token (auth required) |
| `DELETE` | `/api/auth/token` | Revoke the token (auth required) |

Interactive docs: **http://localhost:8000/docs**

---

## Frontend

Open **http://localhost** (Docker) or `npm run dev` at http://localhost:5173.

The React app shows a login page on first visit. After registering or signing in:

- **Orders tab** — filterable table scoped to your business, with create / update / cancel / refund actions
- **API Access tab** — view/copy your Bearer token, regenerate or revoke it, and get ready-to-paste MCP configuration

To run locally for development:

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000`.

---

## Connecting to Claude Code (CLI)

The project ships a `.mcp.json` at the root — Claude Code auto-loads it when you run `claude` inside the project folder.

### Option A — HTTP (recommended, requires Docker stack running)

Update `.mcp.json` with your token:

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

Get your token from the web UI (API Access tab) or:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Business", "password": "yourpassword"}'
```

### Option B — stdio (no Docker required for the MCP layer)

```json
{
  "mcpServers": {
    "order-system": {
      "command": "/path/to/order-mcp/.venv/bin/python",
      "args": ["/path/to/order-mcp/backend/mcp_server.py"],
      "cwd": "/path/to/order-mcp/backend",
      "env": {
        "MCP_BUSINESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

> **Note:** The database must still be reachable (Docker db service or local PostgreSQL).

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
        "PYTHONPATH": "/path/to/order-mcp/backend",
        "MCP_BUSINESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

Then **fully quit (⌘Q) and reopen** Claude Desktop.

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

## Multi-tenancy

Each business has complete data isolation:

- **Registration** creates a `businesses` row with a bcrypt-hashed password and issues an API token.
- **Every API and MCP request** must include `Authorization: Bearer <token>`. The token is validated and mapped to a `business_id`.
- **Orders are filtered by `business_id`** at the database level — a business can never read or modify another business's orders, even if they know the order ID.
- **MCP HTTP transport** (`/mcp`) is protected by `MCPAuthMiddleware` which validates the token and injects the business context before any tool runs.
- **MCP stdio transport** (`mcp_server.py`) reads `MCP_BUSINESS_TOKEN` at startup and applies the same business scope to all tool calls.

---

## License

MIT
