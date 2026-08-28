# mcp_server/main.py
from mcp_server.server import mcp
from config.database import db_connection
import asyncio

import mcp_server.product   # "product" ki jagah "mcp_server.product"
import mcp_server.order
import mcp_server.user

if __name__ == "__main__":
    asyncio.run(db_connection.init_db())
    mcp.run()