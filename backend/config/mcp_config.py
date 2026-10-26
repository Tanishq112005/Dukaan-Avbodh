import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_USER_URL = os.getenv("MCP_USER_SERVER_URL", "http://127.0.0.1:8001/sse")
FASTMCP_TOKEN = os.getenv("FASTMCP_TOKEN")


def _detect_transport(url: str) -> str:
    if "/sse" in url:
        return "sse"
    return "streamable_http"


mcp_user_config = {
    "url": MCP_USER_URL,
    "transport": _detect_transport(MCP_USER_URL),
}

if FASTMCP_TOKEN:
    mcp_user_config["headers"] = {"Authorization": f"Bearer {FASTMCP_TOKEN}"}

mcp_user_client = MultiServerMCPClient({"dukaan": mcp_user_config})
