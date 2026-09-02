# mcp_server/main.py
import sys
import os
import asyncio

# Fix Python path for cloud deployments so it finds 'mcp_server' and backend modules
mcp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.dirname(mcp_dir)
sys.path.insert(0, mcp_dir)
sys.path.insert(0, backend_dir)

# Windows par asyncpg (SSL connections) ProactorEventLoop ke saath fail hota hai
# (ConnectionResetError: WinError 64/10054). Selector loop policy set karna hoga,
# kisi bhi asyncio loop ke banne se PEHLE — tool calls (jo Postgres se baat
# karte hain) is process ke andar isi loop policy se chalenge.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp_server_user.server import mcp

import mcp_server_user.product
import mcp_server_user.order
import mcp_server_user.user

# Naye imports add karo:
import mcp_server_user.pricing

# Track 1+2 unification ke naye tools:
import mcp_server_user.cart
import mcp_server_user.recommendation
import mcp_server_user.search

if __name__ == "__main__":
    print("[READY] Starting MCP Server on http://127.0.0.1:8001 (SSE)")
    mcp.run(transport="sse", port=8001)
