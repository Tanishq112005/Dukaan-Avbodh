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
    of the LangGraph user chat agent.
    """

    def __init__(self, max_retries: int = 2):
        self.agent: Optional[Any] = None  
        self.tools_by_name: Dict[str, Any] = {}
        self.max_retries: int = max_retries

    async def init_agent(self) -> Any:
        """
        Fetches tools from the MCP server, initializes LLMs, 
        and compiles the LangGraph agent.
        """
        logger.info("Initializing User Agent Graph...")
        tools: Optional[List[Any]] = None

        # Quick attempt to connect to MCP user server if running
        for attempt in range(self.max_retries):
            try:
                tools = await mcp_user_client.get_tools()
                if tools is not None:
                    break
            except Exception as e:
                logger.info(
                    f"[Attempt {attempt + 1}/{self.max_retries}] "
                    f"Remote MCP server check: {e}"
                )
                if attempt + 1 < self.max_retries:
                    await asyncio.sleep(1)

        # Fallback if remote MCP server is offline
        if not tools:
            logger.info("Remote MCP server offline or not configured. Using local direct tool suites.")
            from Auth.tools import get_auth_langchain_tools
            from Cart.tools import get_cart_langchain_tools
            from Negotiation.tools import get_negotiation_langchain_tools
            from Order.tools import get_order_langchain_tools
            from Recommedation.tools import get_recommendation_langchain_tools
            from Payment.tools import get_payment_langchain_tools

            direct_tools = (
                get_auth_langchain_tools()
                + get_cart_langchain_tools()
                + get_negotiation_langchain_tools()
                + get_order_langchain_tools()
                + get_recommendation_langchain_tools()
                + get_payment_langchain_tools()
            )
            self.tools_by_name = {t.name: t for t in direct_tools}
            tool_names = ", ".join(sorted(self.tools_by_name.keys()))
            logger.info(f"{len(direct_tools)} direct local tools loaded: {tool_names}")
        else:
            self.tools_by_name = {t.name: t for t in tools}
            tool_names = ", ".join(sorted(self.tools_by_name.keys()))
            logger.info(f"{len(tools)} remote tools fetched: {tool_names}")

        # Initialize LLMs
        logger.info("Initializing LLM models...")
        large_llm = chatModel._large_chat_model()
        medium_llm = chatModel._medium_chat_model()  
        small_llm = chatModel._small_chat_model()

        # Compile the agent graph
        logger.info("Compiling User LangGraph agent...")
        self.agent = compile_agent_graph(
            large_llm, 
            medium_llm, 
            small_llm, 
            self.tools_by_name
        )
        logger.info("User Agent compiled successfully.")

        return self.agent

    async def get_agent_async(self) -> Any:
        """
        Retrieves the compiled agent, lazily initializing it if not yet compiled.
        """
        if self.agent is None:
            await self.init_agent()
        return self.agent

    def get_agent(self) -> Any:
        """
        Retrieves the compiled agent, lazily initializing if not yet compiled.
        """
        if self.agent is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self.init_agent()).result()
            else:
                return asyncio.run(self.init_agent())
        return self.agent


agentService = AgentService()
agent_service = agentService
