import asyncio
import logging
from typing import Optional, Dict, Any, List

from config.chatModel import chatModel
from agents.merchant.graph import compile_agent_graph, resolve_all_merchant_tools

logger = logging.getLogger(__name__)


class MerchantAgentService:
    """
    Service class to handle the initialization and retrieval
    of the unified LangGraph merchant administration & analytics agent.
    Equipped with all 7 native store tools via direct function calling.
    """

    def __init__(self):
        self.agent: Optional[Any] = None
        self.tools_by_name: Dict[str, Any] = {}

    async def init_agent(self) -> Any:
        """
        Loads native merchant tools, binds them via function calling to the chat model,
        and compiles the unified LangGraph agent.
        """
        logger.info("[MERCHANT AGENT] Loading native store tools directly...")
        self.tools_by_name = resolve_all_merchant_tools()
        tool_names = ", ".join(sorted(self.tools_by_name.keys()))
        logger.info(f"[MERCHANT AGENT] {len(self.tools_by_name)} native tools registered: {tool_names}")

        if hasattr(chatModel, "get_large_chat_model"):
            fast_llm = chatModel.get_large_chat_model()
        elif hasattr(chatModel, "_large_chat_model"):
            fast_llm = chatModel._large_chat_model()
        else:
            fast_llm = chatModel.get_chat_model()
        self.agent = compile_agent_graph(fast_llm, self.tools_by_name)
        logger.info("[MERCHANT AGENT] Unified LangGraph merchant agent compiled successfully.")
        return self.agent

    async def get_agent_async(self) -> Any:
        """Retrieves compiled agent, lazily initializing if not yet compiled."""
        if self.agent is None:
            await self.init_agent()
        return self.agent

    def get_agent(self) -> Any:
        """Retrieves compiled agent synchronously, lazily initializing if needed."""
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


# Singleton instance
merchant_agent_service = MerchantAgentService()


# Backward-compatible function interfaces for main.py, Merchant.controller, etc.
async def init_merchant_agent() -> Any:
    return await merchant_agent_service.init_agent()


def get_merchant_agent() -> Any:
    return merchant_agent_service.get_agent()
