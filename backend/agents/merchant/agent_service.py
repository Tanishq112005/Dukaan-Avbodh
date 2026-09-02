import os
import sys
import asyncio
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from agents.merchant.agent_state import AgentState
from config.chatModel import chatModel
from config.mogodbconfig import nosql_client
from langgraph.checkpoint.mongodb import MongoDBSaver
from agents.merchant.agent_prompts import get_system_prompt, get_system_reminder
from agents.merchant.agent_graph import compile_agent_graph
from config.mcp_config import mcp_merchant_client


_merchant_agent = None
_merchant_tools_by_name: dict = {}


async def init_merchant_agent():
    global _merchant_agent, _merchant_tools_by_name

    print("    FastMCP Cloud/Local Server se merchant tools load ho rahe hain...")
    
    max_retries = 10
    tools = None
    
    for attempt in range(max_retries):
        try:
            tools = await mcp_merchant_client.get_tools()
            if tools is not None:
                break
        except Exception as e:
            print(f"   [Attempt {attempt+1}/{max_retries}] Waiting for MCP server... Error string: {e}")
            await asyncio.sleep(2)
            
    if tools is None:
        print("    MCP Server target offline! Activating empty tools fallback to prevent FastAPI crash.")
        tools = []
        _merchant_tools_by_name = {}
    else:
        _merchant_tools_by_name = {t.name: t for t in tools}
        print(f"    {len(tools)} tools mile: {', '.join(sorted(_merchant_tools_by_name.keys()))}")

    print("    LLM ke saath merchant tools bind ho rahe hain...")
    fast_llm = chatModel.get_chat_model()
    if tools:
        fast_llm = fast_llm.bind_tools(tools)
    else:
        print("    LLM operational without active server tools connection.")

    print("    LangGraph merchant agent compile ho raha hai...")
    
    _merchant_agent = compile_agent_graph(fast_llm, _merchant_tools_by_name)
    print("    Merchant Agent compiled successfully with MongoDB per-user memory attached.")
    return _merchant_agent


def get_merchant_agent():
    if _merchant_agent is None:
        raise RuntimeError(
            "Merchant Agent is not initialized. 'await agent_service.init_merchant_agent()' must be called on startup."
        )
    return _merchant_agent
