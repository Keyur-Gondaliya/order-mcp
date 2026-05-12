"""
Order System MCP Server — stdio transport
==========================================
For Claude Code / Claude Desktop local connections.
HTTP transport is also available via the FastAPI app at /mcp.

Usage:
    MCP_BUSINESS_TOKEN=<your-token> python mcp_server.py

MCP_BUSINESS_TOKEN identifies which business's orders this server instance
can access. Get a token by registering at http://localhost:8000/api/auth/register
or from the web UI at http://localhost.
"""

import os
import sys

from app.db.init import init_db
from app.mcp import mcp, set_stdio_business_id
from app.services.tokens import validate_token

if __name__ == "__main__":
    init_db()

    token = os.environ.get("MCP_BUSINESS_TOKEN", "").strip()
    if token:
        business_id = validate_token(token)
        if business_id:
            set_stdio_business_id(business_id)
        else:
            print(
                "Warning: MCP_BUSINESS_TOKEN is invalid or expired. "
                "Tool calls will fail until a valid token is set.",
                file=sys.stderr,
            )
    else:
        print(
            "Warning: MCP_BUSINESS_TOKEN is not set. "
            "Set it to your business API token so tools can access your orders.",
            file=sys.stderr,
        )

    mcp.run(transport="stdio")
