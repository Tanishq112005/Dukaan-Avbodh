import sys
import os
import asyncio
from fastmcp import FastMCP

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

try:
    import mcp as _official_mcp
    if hasattr(_official_mcp, "__path__") and mcp_dir not in _official_mcp.__path__:
        _official_mcp.__path__.append(mcp_dir)
except Exception:
    pass

# Fix Windows ProactorEventLoop SSL issue with asyncpg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialize FastMCP Server for Customer / User Tools
mcp = FastMCP("Dukaan User MCP Server")


def load_user_tools():
    """Imports all customer tools and resources to register them on the FastMCP instance."""
    import Auth.tools
    import Cart.tools
    import Negotiation.tools
    import Order.tools
    import Recommedation.tools
    import Payment.tools


if __name__ == "__main__":
    load_user_tools()
    print("[READY] Starting User FastMCP Server on http://127.0.0.1:8001 (SSE)")
    mcp.run(transport="sse", port=8001)
