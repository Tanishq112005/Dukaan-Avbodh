import os
import sys
import asyncio
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from agents.user.agentState import AgentState
from config.chatModel import chatModel
from repositories.cart_repository import cart_repository
from config.mogodbconfig import nosql_client
from langgraph.checkpoint.mongodb import MongoDBSaver
from agents.user.agent_prompts import get_system_prompt, get_system_reminder
from agents.user.agent_graph import compile_agent_graph
from config.mcp_config import mcp_user_client


_checkout_agent = None
_tools_by_name: dict = {}


async def init_agent():
    global _checkout_agent, _tools_by_name

    print("    FastMCP Cloud/Local Server se tools load ho rahe hain...")
    
    max_retries = 10
    tools = None
    
    for attempt in range(max_retries):
        try:
            tools = await mcp_user_client.get_tools()
            if tools is not None:
                break
        except Exception as e:
            print(f"   [Attempt {attempt+1}/{max_retries}] Waiting for MCP server... Error string: {e}")
            await asyncio.sleep(2)
            
    if tools is None:
        print("    MCP Server target offline! Activating empty tools fallback to prevent FastAPI crash.")
        tools = []
        _tools_by_name = {}
    else:
        _tools_by_name = {t.name: t for t in tools}
        print(f"    {len(tools)} tools mile: {', '.join(sorted(_tools_by_name.keys()))}")

    print("    LLM ke saath tools bind ho rahe hain...")
    fast_llm = chatModel.get_chat_model()
    if tools:
        fast_llm = fast_llm.bind_tools(tools)
    else:
        print("    LLM operational without active server tools connection.")

    print("    LangGraph agent compile ho raha hai...")
    
    _checkout_agent = compile_agent_graph(fast_llm, _tools_by_name)
    print("    Agent compiled successfully with MongoDB per-user memory attached.")
    return _checkout_agent


def get_agent():
    if _checkout_agent is None:
        raise RuntimeError(
            "Agent is not initialized. 'await agent_service.init_agent()' must be called on startup."
        )
    return _checkout_agent