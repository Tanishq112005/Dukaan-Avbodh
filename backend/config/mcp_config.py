import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/sse")
FASTMCP_TOKEN = os.getenv("FASTMCP_TOKEN")

### this is for the fastmcp server to connect to the mcp server, if you are running the mcp server locally, you can set the FASTMCP_TOKEN in your .env file to match the token in the mcp server config. If you are running the mcp server on a remote server, you can set the FASTMCP_TOKEN to any value, as long as it matches the token in the mcp server config.
mcp_config = {
    "url": MCP_URL,
    "transport": "streamable_http",
}

### for the local host mcp_config 
mcp_config_local = {
    "url" : MCP_URL , 
    "transport" : "sse"
}
if FASTMCP_TOKEN:
    mcp_config["headers"] = {
        "Authorization": f"Bearer {FASTMCP_TOKEN}"
    }

### for the local connect 
mcp_client = MultiServerMCPClient({
    "dukaan": mcp_config_local
})
