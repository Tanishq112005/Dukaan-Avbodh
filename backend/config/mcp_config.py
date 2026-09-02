import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_USER_URL = os.getenv("MCP_USER_SERVER_URL", "http://127.0.0.1:8001/sse")
FASTMCP_TOKEN = os.getenv("FASTMCP_TOKEN")
MCP_MERCHANT_URL = os.getenv("MCP_MERCHANT_SERVER_URL", "http://127.0.0.1:8002/sse")




mcp_merchant_config= {
    "url" : MCP_MERCHANT_URL , 
    "transport" : "streamable_http"
}


mcp_user_config = {
    "url": MCP_USER_URL,
    "transport": "streamable_http",
}




if FASTMCP_TOKEN:
    mcp_user_config["headers"] = {
        "Authorization": f"Bearer {FASTMCP_TOKEN}"
    }
    
    mcp_merchant_config["headers"] = {
        "Authorization": f"Bearer {FASTMCP_TOKEN}"
    }
    


mcp_user_client = MultiServerMCPClient({
    "dukaan": mcp_user_config
})

mcp_merchant_client = MultiServerMCPClient({
    "merchant_dukaan": mcp_merchant_config
})