import os
import sys
import logging
from typing import Optional, Dict, Any, List

from config.chatModel import chatModel
from agents.merchant.agent_graph import compile_agent_graph
from Merchant.tools import get_merchant_langchain_tools

logger = logging.getLogger(__name__)

_merchant_agent = None
_merchant_tools_by_name: Dict[str, Any] = {}


async def init_merchant_agent():
    """
    Initializes the single unified Merchant Agent using direct native function tool calling.
    Completely independent of external FastMCP processes with zero network latency.
    """
    global _merchant_agent, _merchant_tools_by_name

    print("\n" + "-" * 55)
    print("    [MERCHANT AGENT] Loading native store tools directly...")
    
    # 1. Load native Python StructuredTools from Merchant domain
    native_tools = get_merchant_langchain_tools()
    _merchant_tools_by_name = {t.name: t for t in native_tools}
    tool_names = ", ".join(sorted(_merchant_tools_by_name.keys()))
    print(f"    [MERCHANT AGENT] {len(native_tools)} native tools registered: {tool_names}")

    # 2. Bind tools directly to LLM via native function calling
    print("    [MERCHANT AGENT] Binding tools directly to LLM for function calling...")
    fast_llm = chatModel.get_chat_model()
    llm_with_tools = fast_llm.bind_tools(native_tools)

    # 3. Compile the single unified LangGraph merchant agent
    print("    [MERCHANT AGENT] Compiling unified LangGraph state graph...")
    _merchant_agent = compile_agent_graph(llm_with_tools, _merchant_tools_by_name)
    print("    [MERCHANT AGENT] Merchant Agent compiled successfully with MongoDB memory attached.")
    print("-" * 55 + "\n")
    return _merchant_agent


def get_merchant_agent():
    """Retrieves the active compiled Merchant Agent instance."""
    global _merchant_agent
    if _merchant_agent is None:
        raise RuntimeError(
            "Merchant Agent is not initialized. 'await agent_service.init_merchant_agent()' must be called on startup."
        )
    return _merchant_agent
