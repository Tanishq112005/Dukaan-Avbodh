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

from repositories.cart_repository import cart_repository

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

    # Fetch cart items to provide context to the LLM
    cart_items = await cart_repository.get_cart_items(state.get("user_id", 0))
    cart_desc = ", ".join([f"{item['name']} (x{item.get('qty', 1)})" for item in cart_items]) if cart_items else "Empty"

    system_prompt = """You are an elite AI Salesperson for 'Dukaan', a premium e-commerce store.
Your goal is to provide exceptional customer service while maximizing the merchant's profit.

CORE INSTRUCTIONS:
1. TONE & POLITENESS: Always remain calm, empathetic, and exceptionally polite, no matter how angry or impatient the customer gets.
2. DOMAIN STRICTNESS: You ONLY talk about shopping at Dukaan. If asked about unrelated topics, politely decline and steer the conversation back to shopping.
3. LANGUAGE: You must ONLY communicate in English.
4. NEGOTIATION MASTERCLASS: When a user asks for a discount, act as a master salesperson. Use the `negotiate_discount_tool`. Try to make them accept the lowest possible discount. Use praise and flattery to make them feel special.
5. SEARCH & RECOMMENDATIONS: 
   - When a user asks for something specific (e.g. "t-shirts"), ALWAYS use `search_products_tool`. Do not pretend to search without using the tool!
   - Look at the user's Cart Contents below. If they have men's items, assume they are shopping for men and append "men's" to your search queries. If women's, append "women's".
   - If the user explicitly rejects your suggestions ("I don't like these"), DO NOT just apologize and ask questions! You MUST immediately use `search_products_tool` with a new, broad query (like "trending", "new arrivals", or a different category) to show them fresh options instantly!
6. NO GUESSING: Do not guess products. Always rely on the tool results.
7. DO NOT REPEAT YOURSELF: Never send the exact same message or suggestions multiple times. Only call a tool ONCE per turn. Do not call the same tool in parallel.
8. PRODUCT DISPLAY: When you use a tool that returns products (search_products or recommend_products), DO NOT manually list the products, their names, prices, or links in your text response. The UI will automatically display rich product cards below your message. Just write a short, engaging conversational sentence like "Here are some great options I found for you!"

Your current state:
- User ID: {user_id}
- Current Discount Offered: {current_discount}%
- Cart Contents: {cart_desc}
"""
    sys_msg = SystemMessage(content=system_prompt.format(
        user_id=state.get("user_id", 0), 
        current_discount=state.get("current_discount_percent", 0.0),
        cart_desc=cart_desc
    ))
    
    # Back Injection System Reminder
    reminder = """[SYSTEM REMINDER: English ONLY. Negotiate fiercely to protect profit. Use the cart's gender to guide your search queries. If a proactive [SYSTEM EVENT] occurs, ALWAYS show new suggestions. Do NOT manually list products; the UI will show them.]"""
    
    mod_messages = [sys_msg] + modified_messages + [SystemMessage(content=reminder)]
    
    response = await fast_llm.ainvoke(mod_messages)
    
    updates = {
        "messages": [response],
        "final_response": response.content if not response.tool_calls else ""
    }
    
    # Clear old suggestions if this is a fresh user request, so we don't carry over old ones.
    # If the last message was a ToolMessage, it means we just got new suggestions, so don't clear them!
    if messages and isinstance(messages[-1], HumanMessage):
        updates["suggested_products"] = []
        
    return updates


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
                    updates["suggested_products"] = res.get("products", [])
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
                    updates["suggested_products"] = res.get("suggested_products", [])
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
