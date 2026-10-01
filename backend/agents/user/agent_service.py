import asyncio
import logging
from typing import Optional, Dict, Any, List

# Imports from your project structure
from config.chatModel import chatModel
from agents.user.graph import compile_agent_graph
from config.mcp_config import mcp_user_client

# Set up logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentService:
    """
    Service class to handle the initialization and retrieval 
    of the LangGraph checkout agent.
    """
    
    def __init__(self, max_retries: int = 10):
        # Class variables with type hinting
        self.agent: Optional[Any] = None  
        self.tools_by_name: Dict[str, Any] = {}
        self.max_retries: int = max_retries

    async def init_agent(self) -> Any:
        """
        Fetches tools from the MCP server, initializes LLMs, 
        and compiles the LangGraph agent.
        """
        logger.info("Fetching tools from MCP server...")
        tools: Optional[List[Any]] = None
        
        # Retry mechanism for fetching tools
        for attempt in range(self.max_retries):
            try:
                tools = await mcp_user_client.get_tools()
                if tools is not None:
                    break
            except Exception as e:
                logger.warning(
                    f"[Attempt {attempt + 1}/{self.max_retries}] "
                    f"Waiting for MCP server... Error: {e}"
                )
                await asyncio.sleep(2)
        
        # Fallback if tools fail to load
        if tools is None:
            logger.error("MCP Server target offline! Activating empty tools fallback to prevent FastAPI crash.")
            tools = []
            self.tools_by_name = {}
        else:
            self.tools_by_name = {t.name: t for t in tools}
            tool_names = ', '.join(sorted(self.tools_by_name.keys()))
            logger.info(f"{len(tools)} tools fetched: {tool_names}")

        # Initialize LLMs
        logger.info("Initializing LLM models...")
        large_llm = chatModel._large_chat_model()
        medium_llm = chatModel._medium_chat_model()  
        small_llm = chatModel._small_chat_model()
        
        if not tools:
            logger.info("LLM operational without active server tools connection.")

        # Compile the agent graph
        logger.info("Compiling LangGraph agent...")
        self.agent = compile_agent_graph(
            large_llm, 
            medium_llm, 
            small_llm, 
            self.tools_by_name
        )
        logger.info("Agent compiled successfully with MongoDB per-user memory attached.")
        
        return self.agent

    def get_agent(self) -> Any:
        """
        Retrieves the compiled agent. 
        Raises a RuntimeError if called before initialization.
        """
        if self.agent is None:
            raise RuntimeError(
                "Agent is not initialized. 'await agent_service.init_agent()' "
                "must be called on FastAPI startup."
            )
        return self.agent



agent_service = AgentService()