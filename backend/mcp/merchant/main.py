import sys
import os
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp.merchant.server import mcp, load_merchant_tools

if __name__ == "__main__":
    load_merchant_tools()
    port = int(os.environ.get("PORT", 8002))
    print(f"[READY] Starting Merchant FastMCP Server on 0.0.0.0:{port} (SSE)")
    mcp.run(transport="sse", host="0.0.0.0", port=port)
