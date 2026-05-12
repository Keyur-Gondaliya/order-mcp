from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.context import current_business_id
from app.db.init import init_db
from app.mcp import mcp
from app.ratelimit import check as rate_check
from app.routes.auth import router as auth_router
from app.routes.orders import router as orders_router
from app.services import tokens as token_svc

app = FastAPI(title="Order System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)
app.include_router(auth_router)


class MCPAuthMiddleware:
    """ASGI middleware that validates Bearer tokens for /mcp requests
    and sets current_business_id contextvar before passing to the MCP app."""

    def __init__(self, mcp_app):
        self.mcp_app = mcp_app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.mcp_app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        auth = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")

        if not auth.startswith("Bearer "):
            await _send_json_error(send, 401, "Authorization header required (Bearer <token>)")
            return

        token_str = auth[7:].strip()
        loop = asyncio.get_event_loop()
        business_id = await loop.run_in_executor(None, token_svc.validate_token, token_str)

        if business_id is None:
            await _send_json_error(send, 401, "Invalid or expired token")
            return

        allowed, _ = rate_check(business_id)
        if not allowed:
            await _send_json_error(
                send, 429, "Rate limit exceeded. Try again later.",
                extra_headers=[(b"retry-after", str(60).encode())],
            )
            return

        ctx_token = current_business_id.set(business_id)
        try:
            await self.mcp_app(scope, receive, send)
        finally:
            current_business_id.reset(ctx_token)


async def _send_json_error(
    send, status: int, detail: str, extra_headers: list | None = None
) -> None:
    body = json.dumps({"detail": detail}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


# MCP over HTTP — wrapped with auth middleware so each request is scoped to a business
app.mount("/mcp", MCPAuthMiddleware(mcp.streamable_http_app()))


@app.on_event("startup")
def on_startup() -> None:
    init_db()
