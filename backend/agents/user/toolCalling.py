import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agents.user.state import AgentState
from agents.user.prompts import get_system_prompt, get_system_reminder
from repositories.cart_repository import cart_repository





#### fuction for calling the tools from the specialist node , from the mcp server 
#### This functions properly extracts and safe parse it 

### helper functions for extracting text and safely parsing JSON from tool responses
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

### for creating the tools node for the specialist node , this function is used in the agent_graph.py file
def create_tools_node(tools_dict):
    async def tools_node(state: AgentState):
        last_message = state["messages"][-1]
        tool_messages, updates = [], {}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])

            tool = tools_dict.get(tool_name)
            if tool is None:
                print(f"[TOOL ERROR] Unknown tool '{tool_name}'")
                tool_messages.append(ToolMessage(content='{"error": "Unknown tool"}', tool_call_id=tool_call["id"]))
                continue

            # Only auto-inject params the tool's own schema actually accepts,
            # so tools that don't declare user_id/thread_id/etc. (e.g.
            # get_products_by_type) don't get rejected with an
            # "unexpected keyword argument" validation error.
            accepted_params = getattr(tool, "args", {}) or {}

            if "user_id" in accepted_params:
                tool_args["user_id"] = tool_args.get("user_id", state.get("user_id", 0))

            if tool_name in ["negotiate_discount", "create_order", "check_payment_status", "calculate_combo_offer", "recommend_products"]:
                if "thread_id" in accepted_params:
                    tool_args["thread_id"] = state.get("thread_id", str(state.get("user_id", 0)))

            print(f"[TOOL START] Executing '{tool_name}' with args: {tool_args}")

            if tool_name == "negotiate_discount" and "current_discount_percent" not in tool_args and "current_discount_percent" in accepted_params:
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
                    if parsed.get("combo_offer"):
                        updates["combo_offer"] = parsed["combo_offer"]
                elif tool_name == "negotiate_discount":
                    updates["current_discount_percent"] = parsed.get("counter_offer_percent", 0.0)
                    updates["combo_offer"] = parsed.get("combo_offer")
                elif tool_name == "calculate_combo_offer":
                    updates["combo_offer"] = parsed.get("combo_offer")
                elif tool_name in ["add_to_cart", "remove_from_cart", "update_cart_item_quantity", "clear_cart", "decline_combo_offer"]:
                    updates["combo_offer"] = None
                elif tool_name == "create_order":
                    updates["combo_offer"] = None
                    if parsed.get("payment_link"):
                        updates["pending_payment_link"] = parsed.get("payment_link")
                    if parsed.get("payment_link_id"):
                        updates["pending_payment_link_id"] = parsed.get("payment_link_id")
                elif tool_name == "check_payment_status":
                    if parsed.get("paid") is True:
                        updates["pending_payment_link"] = None
                        updates["pending_payment_link_id"] = None

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=tool_call["id"]))

        updates["messages"] = tool_messages
        return updates
    return tools_node




