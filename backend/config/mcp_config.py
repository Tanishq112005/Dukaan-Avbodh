import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/sse")
FASTMCP_TOKEN = os.getenv("FASTMCP_TOKEN")

mcp_config = {
    "url": MCP_URL,
    "transport": "streamable_http",
}

if FASTMCP_TOKEN:
    mcp_config["headers"] = {
        "Authorization": f"Bearer {FASTMCP_TOKEN}"
    }

mcp_client = MultiServerMCPClient({
    "dukaan": mcp_config
})
