# Compatibility forwarder to mcp.user.main
import sys
import os
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp.user.server import mcp

if __name__ == "__main__":
    print("[READY] Starting MCP Server on http://127.0.0.1:8001 (SSE)")
    mcp.run(transport="sse", port=8001)
