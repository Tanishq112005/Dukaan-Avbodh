import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_MERCHANT_URL = os.getenv("MCP_MERCHANT_SERVER_URL", "http://127.0.0.1:8002/sse")

mcp_merchant_config_local = {
    "url" : MCP_MERCHANT_URL , 
    "transport" : "sse"
}

mcp_merchant_client = MultiServerMCPClient({
    "merchant_dukaan": mcp_merchant_config_local
})
