import os
import sys
import asyncio
import logging
from typing import Optional, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from agents.merchant.agent_state import AgentState
from config.chatModel import chatModel
from config.mogodbconfig import nosql_client
from langgraph.checkpoint.mongodb import MongoDBSaver
from agents.merchant.agent_prompts import get_system_prompt, get_system_reminder
from agents.merchant.agent_graph import compile_agent_graph
from config.mcp_config import mcp_merchant_client
from Merchant.tools import get_merchant_langchain_tools

logger = logging.getLogger(__name__)

_merchant_agent = None
_merchant_tools_by_name: Dict[str, Any] = {}


async def init_merchant_agent():
    global _merchant_agent, _merchant_tools_by_name

    logger.info("Initializing Merchant AI Agent with native domain tools...")
    
    # 1. Start with native in-process merchant tools (zero-latency, guaranteed available)
    native_tools = get_merchant_langchain_tools()
    _merchant_tools_by_name = {t.name: t for t in native_tools}
    logger.info("Loaded %d native Merchant domain tools.", len(native_tools))

    # 2. Optionally merge remote FastMCP merchant tools if server is running
    max_retries = 2
    for attempt in range(max_retries):
        try:
            mcp_tools = await mcp_merchant_client.get_tools()
            if mcp_tools:
                for t in mcp_tools:
                    _merchant_tools_by_name[t.name] = t
                logger.info("Connected to remote FastMCP server: %d total tools available.", len(_merchant_tools_by_name))
                break
        except Exception as e:
            if attempt + 1 < max_retries:
                await asyncio.sleep(1)

    combined_tools = list(_merchant_tools_by_name.values())
    tool_names = ", ".join(sorted(_merchant_tools_by_name.keys()))
    print(f"    [MERCHANT AGENT] {len(combined_tools)} tools active: {tool_names}")

    print("    LLM ke saath merchant tools bind ho rahe hain...")
    fast_llm = chatModel.get_chat_model()
    if combined_tools:
        fast_llm = fast_llm.bind_tools(combined_tools)

    print("    LangGraph merchant agent compile ho raha hai...")
    _merchant_agent = compile_agent_graph(fast_llm, _merchant_tools_by_name)
    print("    Merchant Agent compiled successfully with MongoDB per-user memory attached.")
    return _merchant_agent


def get_merchant_agent():
    global _merchant_agent
    if _merchant_agent is None:
        # Fallback synchronous trigger or compile without remote delay
        raise RuntimeError(
            "Merchant Agent is not initialized. 'await agent_service.init_merchant_agent()' must be called on startup."
        )
    return _merchant_agent
