# mcp_server/main.py
from mcp_server.server import mcp
from config.database import db_connection
import asyncio

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
    asyncio.run(db_connection.init_db())
    # streamable-http transport — yeh ab ek standalone, always-running server hai.
    # Chat backend (agent_service.py) isi se MultiServerMCPClient ke through connect
    # karta hai, aur future mein koi bhi external AI agent (Track 2 buyer) bhi
    # isi URL pe connect karke seedha in tools ko call kar sakta hai.
    # Run this as its OWN process, alag se: python -m mcp_server.main
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)