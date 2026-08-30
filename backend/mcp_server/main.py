# mcp_server/main.py
from mcp_server.server import mcp
from config.database import db_connection
import asyncio

import mcp_server.product
import mcp_server.order
import mcp_server.user

# Naye imports add karo:
import mcp_server.behavior
import mcp_server.pricing

# Track 1+2 unification ke naye tools:
import mcp_server.cart
import mcp_server.recommendation
import mcp_server.search

if __name__ == "__main__":
    asyncio.run(db_connection.init_db())
    mcp.run()