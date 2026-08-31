# mcp_server/main.py
import sys
import asyncio

# Windows par asyncpg (SSL connections) ProactorEventLoop ke saath fail hota hai
# (ConnectionResetError: WinError 64/10054). Selector loop policy set karna hoga,
# kisi bhi asyncio loop ke banne se PEHLE — tool calls (jo Postgres se baat
# karte hain) is process ke andar isi loop policy se chalenge.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp_server.server import mcp

import mcp_server.product
import mcp_server.order
import mcp_server.user

# Naye imports add karo:
import mcp_server.pricing

# Track 1+2 unification ke naye tools:
import mcp_server.cart
import mcp_server.recommendation
import mcp_server.search

if __name__ == "__main__":
    # DB tables banane ki zaroorat NAHI hai yahan — woh already backend/main.py
    # (FastAPI app) ke startup event mein ho chuka hoga. Do alag processes se
    # ek hi migration dobara chalana (a) redundant hai, aur (b) Windows par yeh
    # extra fresh connection asyncpg/SSL ke saath flaky nikla — isliye skip.
    #
    # TESTING/DEV: abhi stdio transport (default) — MultiServerMCPClient isi
    # script ko subprocess ki tarah spawn karke stdin/stdout se baat karega.
    # Baad mein production/Track-2 (external agents) ke liye streamable-http
    # pe shift karenge: mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
    mcp.run()
