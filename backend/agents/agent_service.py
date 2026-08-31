# agents/agent_service.py
import os
import sys
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.agentState import AgentState
from config.chatModel import chatModel
from repositories.cart_repository import cart_repository


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

mcp_client = MultiServerMCPClient(
    {
        "dukaan": {
            "command": sys.executable,
            "args": ["-m", "mcp_server.main"],
            "cwd": BACKEND_DIR,
            "transport": "stdio",
        }
    }
)


_checkout_agent = None
_tools_by_name: dict = {}


def _extract_text(res) -> str:
    """MultiServerMCPClient se aaya raw tool result kisi bhi shape mein ho sakta
    hai (string, content-block list, ya (content, artifact) tuple) — isse ek
    plain JSON string mein normalize karta hai, taaki ToolMessage aur parsing
    dono ke liye consistent format mile."""
    if isinstance(res, tuple):
        res = res[0]
    if isinstance(res, list) and res and isinstance(res[0], dict) and "text" in res[0]:
        return res[0]["text"]
    if isinstance(res, str):
        return res
    return json.dumps(res, default=str)


def _safe_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


async def init_agent():
    """Backend startup (main.py) ke waqt EK BAAR call karo. MCP server se saare
    tools LangChain-compatible format mein load karke poora LangGraph agent
    compile kar deta hai."""
    global _checkout_agent, _tools_by_name

    print("   ↳ MCP server (mcp_server/main.py) se connect ho raha hai (stdio subprocess)...")
    tools = await mcp_client.get_tools()
    _tools_by_name = {t.name: t for t in tools}
    print(f"   ↳ {len(tools)} tools mile: {', '.join(sorted(_tools_by_name.keys()))}")

    print("   ↳ LLM ke saath tools bind ho rahe hain...")
    fast_llm = chatModel.get_chat_model().bind_tools(tools)

    print("   ↳ LangGraph agent (agent ↔ tools loop) compile ho raha hai...")

    async def agent_node(state: AgentState):
        messages = list(state["messages"])

        # Translate ALL background triggers in history so LLM doesn't get confused
        modified_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content == "PROACTIVE_SUGGESTION_TRIGGER":
                modified_messages.append(HumanMessage(content="[SYSTEM EVENT: The user is browsing or idle. Please call recommend_products to show them some suggestions and pitch them proactively.]"))
            else:
                modified_messages.append(msg)

        cart_items = await cart_repository.get_cart_items(state.get("user_id", 0))
        cart_desc = ", ".join([f"{item['name']} (x{item.get('quantity', 1)})" for item in cart_items]) if cart_items else "Empty"

        system_prompt = """You are an elite AI Salesperson for 'Dukaan', a premium e-commerce store.
Your goal is to provide exceptional customer service while maximizing the merchant's profit.

CORE INSTRUCTIONS:
1. TONE & POLITENESS: Always remain calm, empathetic, and exceptionally polite, no matter how angry or impatient the customer gets.
2. DOMAIN STRICTNESS: You ONLY talk about shopping at Dukaan. If asked about unrelated topics, politely decline and steer the conversation back to shopping.
3. LANGUAGE: You must ONLY communicate in English.
4. NEGOTIATION MASTERCLASS: When a user asks for a discount (mentions "discount", "%", "off", "deal", or a price they want), this is your TOP PRIORITY for this turn — do NOT recommend unrelated products instead. First call `get_cart` if you don't already know the cart contents, then call `negotiate_discount` with those cart_items. Try to make them accept the lowest possible discount. Use praise and flattery to make them feel special.
5. CART MANAGEMENT: Use `add_to_cart`, `remove_from_cart`, and `update_cart_item_quantity` whenever the user asks to add/remove/change something in their cart. Use `get_cart` whenever you need to know what's currently in the cart.
6. SEARCH & RECOMMENDATIONS:
   - When a user asks for something specific (e.g. "t-shirts"), ALWAYS use `search_products`. Do not pretend to search without using the tool!
   - Look at the user's Cart Contents below. If they have men's items, assume they are shopping for men and append "men's" to your search queries. If women's, append "women's".
   - If the user explicitly rejects your suggestions ("I don't like these"), DO NOT just apologize and ask questions! You MUST immediately use `search_products` with a new, broad query (like "trending", "new arrivals", or a different category) to show them fresh options instantly!
7. NO GUESSING: Do not guess products. Always rely on the tool results.
8. DO NOT REPEAT YOURSELF: Never send the exact same message or suggestions multiple times. Only call a tool ONCE per turn. Do not call the same tool in parallel.
9. PRODUCT DISPLAY: When you use a tool that returns products (search_products or recommend_products), DO NOT manually list the products, their names, prices, or links in your text response. The UI will automatically display rich product cards below your message. Just write a short, engaging conversational sentence like "Here are some great options I found for you!"

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

        reminder = """[SYSTEM REMINDER: English ONLY. Negotiate fiercely to protect profit. Use the cart's gender to guide your search queries. If a proactive [SYSTEM EVENT] occurs, ALWAYS show new suggestions. Do NOT manually list products; the UI will show them.]"""

        mod_messages = [sys_msg] + modified_messages + [SystemMessage(content=reminder)]

        response = await fast_llm.ainvoke(mod_messages)

        if response.tool_calls:
            called = ', '.join(tc["name"] for tc in response.tool_calls)
            print(f"🤖 Agent ne decide kiya: tool(s) call karo → {called}")
        else:
            preview = (response.content or "")[:80]
            print(f"🤖 Agent ne seedha reply diya (koi tool nahi): \"{preview}...\"" if len(response.content or "") > 80 else f"🤖 Agent ne seedha reply diya (koi tool nahi): \"{preview}\"")

        updates = {
            "messages": [response],
            "final_response": response.content if not response.tool_calls else ""
        }

        if messages and isinstance(messages[-1], HumanMessage):
            updates["suggested_products"] = []

        return updates

    async def tools_node(state: AgentState):
        last_message = state["messages"][-1]
        tool_messages = []
        updates = {}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])

            if "user_id" not in tool_args:
                tool_args["user_id"] = state.get("user_id", 0)

            tool = _tools_by_name.get(tool_name)
            if tool is None:
                print(f"   ❌ Unknown tool call: {tool_name}")
                tool_messages.append(ToolMessage(content='{"error": "Unknown tool"}', tool_call_id=tool_call["id"]))
                continue

            # negotiate_discount ke liye safety net: agar LLM current_discount_percent
            # ya cart_items bhejna bhool jaaye, server khud fill kar deta hai
            if tool_name == "negotiate_discount":
                if "current_discount_percent" not in tool_args:
                    tool_args["current_discount_percent"] = state.get("current_discount_percent", 0.0)
                if not tool_args.get("cart_items"):
                    db_cart = await cart_repository.get_cart_items(state.get("user_id", 0))
                    tool_args["cart_items"] = [
                        {"product_id": item["product_id"], "quantity": item["quantity"]}
                        for item in db_cart
                    ]

            print(f"   🔧 Calling tool: {tool_name}({tool_args})")
            try:
                raw_res = await tool.ainvoke(tool_args)
            except Exception as e:
                print(f"   ❌ Tool '{tool_name}' fail ho gaya: {e}")
                tool_messages.append(ToolMessage(content=f'{{"error": "{str(e)}"}}', tool_call_id=tool_call["id"]))
                continue

            res_text = _extract_text(raw_res)
            parsed = _safe_parse(res_text)
            ok = isinstance(parsed, dict) and parsed.get("success")
            print(f"   {'✅' if ok else '⚠️'} Tool '{tool_name}' se result mila (success={ok}).")

            if isinstance(parsed, dict) and parsed.get("success"):
                if tool_name == "search_products":
                    updates["suggested_products"] = parsed.get("products", [])
                elif tool_name == "recommend_products":
                    updates["suggested_products"] = parsed.get("suggested_products", [])
                elif tool_name == "negotiate_discount":
                    updates["current_discount_percent"] = parsed.get("counter_offer_percent", 0.0)
                    if "combo_offer" in parsed:
                        updates["combo_offer"] = parsed["combo_offer"]

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=tool_call["id"]))

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
    _checkout_agent = workflow.compile(checkpointer=memory)
    print("   ↳ Agent compile ho gaya, memory (per-user conversation history) attach ho gayi.")
    return _checkout_agent


def get_agent():
    """chat_routes.py isse call karta hai. init_agent() startup pe already ho
    chuka hoga, isliye yeh sirf cached compiled graph return karta hai."""
    if _checkout_agent is None:
        raise RuntimeError(
            "Agent abhi initialize nahi hua. main.py ke startup event mein "
            "'await agent_service.init_agent()' call hona chahiye, aur MCP server "
            "(python -m mcp_server.main) alag se already chal raha hona chahiye."
        )
    return _checkout_agent
