# services/agent_service.py
import json
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.agentState import AgentState
from config.chatModel import chatModel
from langchain_core.tools import tool

# Import the MCP Tools
from mcp_server.search import search_products
from mcp_server.pricing import negotiate_discount
from mcp_server.recommendation import recommend_products

# Wrap MCP tools as LangChain Tools
@tool
async def search_products_tool(user_id: int, query: str, category: str = None):
    """Searches for products based on a specific query or style."""
    return await search_products(user_id=user_id, query=query, category=category)

@tool
async def negotiate_discount_tool(user_id: int, current_discount_percent: float, requested_discount_percent: float, is_angry: bool = False):
    """Negotiates a discount. MUST pass the current_discount_percent from your state."""
    return await negotiate_discount(user_id=user_id, current_discount_percent=current_discount_percent, requested_discount_percent=requested_discount_percent, is_angry=is_angry)

@tool
async def recommend_products_tool(user_id: int):
    """Recommends products to the user based on their behavior, affinity, and cart."""
    return await recommend_products(user_id=user_id)

tools = [search_products_tool, negotiate_discount_tool, recommend_products_tool]
fast_llm = chatModel.get_chat_model().bind_tools(tools)


async def agent_node(state: AgentState):
    messages = list(state["messages"])
    
    # Translate ALL background triggers in history so LLM doesn't get confused by past ones
    modified_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content == "PROACTIVE_SUGGESTION_TRIGGER":
            modified_messages.append(HumanMessage(content="[SYSTEM EVENT: The user is browsing or idle. Please call recommend_products_tool to show them some suggestions and pitch them proactively.]"))
        else:
            modified_messages.append(msg)

    system_prompt = """You are an elite AI Salesperson for 'Dukaan', a premium e-commerce store.
Your goal is to provide exceptional customer service while maximizing the merchant's profit.

CORE INSTRUCTIONS:
1. TONE & POLITENESS: Always remain calm, empathetic, and exceptionally polite, no matter how angry or impatient the customer gets.
2. DOMAIN STRICTNESS: You ONLY talk about shopping at Dukaan. If asked about unrelated topics, politely decline and steer the conversation back to shopping.
3. LANGUAGE: You must ONLY communicate in English.
4. NEGOTIATION MASTERCLASS: When a user asks for a discount, act as a master salesperson. Use the `negotiate_discount_tool`. Try to make them accept the lowest possible discount. Use praise and flattery to make them feel special.
5. TOOL MASTERY: Use `search_products_tool` when they want something specific. Use `recommend_products_tool` when they need inspiration or ask for suggestions.
6. NO GUESSING: Do not guess what is in their cart, the tools will fetch it automatically.
7. DO NOT REPEAT YOURSELF: Never send the exact same message or suggestions multiple times. Only call a tool ONCE per turn. Do not call the same tool in parallel.

Your current state:
- User ID: {user_id}
- Current Discount Offered: {current_discount}%
"""
    sys_msg = SystemMessage(content=system_prompt.format(
        user_id=state.get("user_id", 0), 
        current_discount=state.get("current_discount_percent", 0.0)
    ))
    
    # Back Injection System Reminder
    reminder = """[SYSTEM REMINDER: English ONLY. Be extremely polite. Do NOT answer unrelated questions. Negotiate fiercely to protect profit using the tool, start low and praise the user. Do not guess data by yourself, always use tools. Do NOT repeat previous messages.]"""
    
    mod_messages = [sys_msg] + modified_messages + [SystemMessage(content=reminder)]
    
    response = await fast_llm.ainvoke(mod_messages)
    
    return {
        "messages": [response],
        "final_response": response.content if not response.tool_calls else ""
    }


async def tools_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_messages = []
    updates = {}
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Ensure user_id is injected
        if "user_id" not in tool_args:
            tool_args["user_id"] = state.get("user_id", 0)
            
        try:
            if tool_name == "search_products_tool":
                res = await search_products_tool.ainvoke(tool_args)
                if isinstance(res, dict) and res.get("success"):
                    updates["suggested_product_ids"] = [p["id"] for p in res.get("products", [])]
                tool_messages.append(ToolMessage(content=json.dumps(res), tool_call_id=tool_call["id"]))
                
            elif tool_name == "negotiate_discount_tool":
                if "current_discount_percent" not in tool_args:
                    tool_args["current_discount_percent"] = state.get("current_discount_percent", 0.0)
                res = await negotiate_discount_tool.ainvoke(tool_args)
                if isinstance(res, dict) and res.get("success"):
                    updates["current_discount_percent"] = res.get("counter_offer_percent", 0.0)
                    if "combo_offer" in res:
                        updates["combo_offer"] = res["combo_offer"]
                tool_messages.append(ToolMessage(content=json.dumps(res), tool_call_id=tool_call["id"]))
                
            elif tool_name == "recommend_products_tool":
                res = await recommend_products_tool.ainvoke(tool_args)
                if isinstance(res, dict) and res.get("success"):
                    updates["suggested_product_ids"] = [p["id"] for p in res.get("suggested_products", [])]
                tool_messages.append(ToolMessage(content=json.dumps(res), tool_call_id=tool_call["id"]))
                
            else:
                tool_messages.append(ToolMessage(content='{"error": "Unknown tool"}', tool_call_id=tool_call["id"]))
        except Exception as e:
            tool_messages.append(ToolMessage(content=f'{{"error": "{str(e)}"}}', tool_call_id=tool_call["id"]))
            
    updates["messages"] = tool_messages
    return updates


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

memory = MemorySaver()
checkout_agent = workflow.compile(checkpointer=memory)
