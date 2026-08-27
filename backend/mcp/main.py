from mcp.server import mcp
from config.database import db_connection
import asyncio

import product
import order
import user

if __name__ == "__main__":
    asyncio.run(db_connection.init_db())   # tables create ho jaayengi agar exist nahi karti
    mcp.run()
    