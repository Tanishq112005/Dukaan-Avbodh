import json
import re
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agents.agentState import AgentState
from agents.agent_prompts import get_system_prompt, get_system_reminder
from repositories.cart_repository import cart_repository

def _extract_text(res) -> str:
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

def create_agent_node(fast_llm):
    async def agent_node(state: AgentState):
        messages = list(state["messages"])
        modified_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content == "PROACTIVE_SUGGESTION_TRIGGER":
                modified_messages.append(HumanMessage(content="[SYSTEM EVENT: The frontend is requesting proactive recommendations. Use the `recommend_products` tool immediately.]"))
            else:
                modified_messages.append(msg)

        cart_items = await cart_repository.get_cart_items(state.get("user_id", 0))
        cart_desc = ", ".join([f"{item['name']} (x{item.get('quantity', 1)})" for item in cart_items]) if cart_items else "Empty"

        sys_msg = SystemMessage(content=get_system_prompt(
            user_id=state.get("user_id", 0),
            current_discount=state.get("current_discount_percent", 0.0),
            cart_desc=cart_desc
        ))

        mod_messages = [sys_msg] + modified_messages + [SystemMessage(content=get_system_reminder())]
        response = await fast_llm.ainvoke(mod_messages)

        print(f"\n[AGENT] Generated response.")
        if response.tool_calls:
            print(f"[AGENT] Decided to execute {len(response.tool_calls)} tools: {[t['name'] for t in response.tool_calls]}")
        elif response.content:
            print(f"[AGENT] Sending text response back to user.")

        final_text = response.content if not response.tool_calls else ""
        if final_text:
            final_text = re.sub(r'<thought>.*?</thought>', '', final_text, flags=re.DOTALL).strip()

        updates = {"messages": [response], "final_response": final_text}
        if messages and isinstance(messages[-1], HumanMessage):
            updates["suggested_products"] = []
        return updates
    return agent_node

def create_tools_node(tools_dict):
    async def tools_node(state: AgentState):
        last_message = state["messages"][-1]
        tool_messages, updates = [], {}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])
            tool_args["user_id"] = tool_args.get("user_id", state.get("user_id", 0))

            print(f"[TOOL START] Executing '{tool_name}' with args: {tool_args}")

            tool = tools_dict.get(tool_name)
            if tool is None:
                print(f"[TOOL ERROR] Unknown tool '{tool_name}'")
                tool_messages.append(ToolMessage(content='{"error": "Unknown tool"}', tool_call_id=tool_call["id"]))
                continue

            if tool_name == "negotiate_discount" and "current_discount_percent" not in tool_args:
                tool_args["current_discount_percent"] = state.get("current_discount_percent", 0.0)

            try:
                raw_res = await tool.ainvoke(tool_args)
            except Exception as e:
                print(f"[TOOL ERROR] Exception in '{tool_name}': {str(e)}")
                tool_messages.append(ToolMessage(content=f'{{"error": "{str(e)}"}}', tool_call_id=tool_call["id"]))
                continue

            res_text = _extract_text(raw_res)
            
            # Print truncated result for logging
            log_res = res_text if len(res_text) < 300 else res_text[:300] + "... [TRUNCATED]"
            print(f"[TOOL FINISHED] '{tool_name}' returned: {log_res}")
            
            parsed = _safe_parse(res_text)

            if isinstance(parsed, dict) and parsed.get("success"):
                if "products" in parsed:
                    updates["suggested_products"] = parsed.get("products", [])
                elif tool_name == "recommend_products":
                    updates["suggested_products"] = parsed.get("suggested_products", [])
                elif tool_name == "negotiate_discount":
                    updates["current_discount_percent"] = parsed.get("counter_offer_percent", 0.0)
                    if "combo_offer" in parsed and parsed["combo_offer"].get("effective_discount_percent", 0) > 0:
                        updates["combo_offer"] = parsed["combo_offer"]
                elif tool_name == "calculate_combo_offer" and "combo_offer" in parsed:
                    updates["combo_offer"] = parsed["combo_offer"]

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=tool_call["id"]))

        updates["messages"] = tool_messages
        return updates
    return tools_node
