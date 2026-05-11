from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init import init_db
from app.mcp import mcp
from app.routes.auth import router as auth_router
from app.routes.orders import router as orders_router

app = FastAPI(title="Order System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)
app.include_router(auth_router)

# MCP over HTTP — Claude Desktop / Claude Code can connect via:
#   type: "http"  url: "http://localhost:8000/mcp"
app.mount("/mcp", mcp.streamable_http_app())


@app.on_event("startup")
def on_startup() -> None:
    init_db()
