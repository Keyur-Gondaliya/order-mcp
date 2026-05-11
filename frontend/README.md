# Order Management Frontend

React + Vite frontend for the Order MCP system.

## Development

```bash
npm install
npm run dev    # http://localhost:5173
```

Requires the backend API running on `http://localhost:8000` (the dev server proxies `/api` there).

## Build

```bash
npm run build   # output → dist/
```

## Docker

Built and served automatically by `docker compose up` in the project root. nginx proxies `/api` requests to the backend container.

## Pages

- **Orders** — filterable table; create, update status, cancel, and refund orders
- **API Access** — view/copy/regenerate/revoke the bearer token; MCP JSON config and OAuth command snippets
