"""
Order System MCP Server — stdio transport
==========================================
For Claude Code / Claude Desktop local connections.
HTTP transport is also available via the FastAPI app at /mcp.

Usage:
    python mcp_server.py
"""

from app.db.init import init_db
from app.mcp import mcp

if __name__ == "__main__":
    init_db()
    mcp.run(transport="stdio")
