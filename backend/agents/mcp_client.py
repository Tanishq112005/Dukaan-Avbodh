import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# MCP Server ko as a subprocess (stdio) run karne ka setup
server_params = StdioServerParameters(
    command="python",
    args=["-m", "mcp_server.main"],
    env=None # Uses current environment
)

async def call_mcp_tool(tool_name: str, arguments: dict) -> any:
    """
    Ek universal function jo tumhare LangGraph agent ko 
    MCP Server se connect karega aur tools execute karega.
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Server se connection initialize karo
            await session.initialize()
            
            # Tool call karo
            result = await session.call_tool(tool_name, arguments)
            
            # FastMCP returns a list of text/image contents. We extract the text.
            if result.content and len(result.content) > 0:
                # MCP tools typically return JSON strings in text format
                return result.content[0].text
            return None
