import json
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agents.merchant.agent_state import AgentState
from agents.merchant.agent_prompts import get_system_prompt, get_system_reminder
from utils.text_cleaning import clean_ai_output

logger = logging.getLogger(__name__)


def _extract_text(res: Any) -> str:
    """Extracts a JSON/text string representation from tool execution result."""
    if isinstance(res, tuple):
        res = res[0]
    if isinstance(res, list) and res and isinstance(res[0], dict) and "text" in res[0]:
        return res[0]["text"]
    if isinstance(res, str):
        return res
    return json.dumps(res, default=str)


def _safe_parse(text: str) -> Optional[Dict[str, Any]]:
    """Safely attempts to parse text as a JSON dictionary."""
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def create_agent_node(fast_llm):
    """Creates the primary LLM reasoning node for the Merchant Agent."""
    async def agent_node(state: AgentState):
        messages = list(state.get("messages", []))
        merchant_id = state.get("merchant_id") or state.get("user_id") or 1

        sys_msg = SystemMessage(content=get_system_prompt(user_id=merchant_id))
        mod_messages = [sys_msg] + messages + [SystemMessage(content=get_system_reminder())]

        response = await fast_llm.ainvoke(mod_messages)

        final_text = response.content if not response.tool_calls else ""
        if isinstance(final_text, list):
            final_text = "\n".join([str(x) if isinstance(x, str) else x.get("text", "") for x in final_text if isinstance(x, (str, dict))])
        elif not isinstance(final_text, str):
            final_text = str(final_text)

        if final_text:
            final_text = clean_ai_output(final_text)

        # Detect intent based on response / tool calls
        intent = "general_inquiry"
        if response.tool_calls:
            first_tool = response.tool_calls[0]["name"]
            if "analytics" in first_tool:
                intent = "analytics_inquiry"
            elif "top_selling" in first_tool:
                intent = "top_products_inquiry"
            elif "inventory" in first_tool:
                intent = "inventory_health_check"
            elif "order" in first_tool:
                intent = "order_lookup"
            elif "pricing" in first_tool:
                intent = "pricing_margin_update"
            elif "negotiation" in first_tool:
                intent = "negotiation_insights"
            elif "publish" in first_tool:
                intent = "publish_catalog_item"

        updates: Dict[str, Any] = {
            "messages": [response],
            "final_response": final_text,
            "current_intent": intent,
            "merchant_id": merchant_id,
            "user_id": merchant_id,
        }
        return updates

    return agent_node


def create_tools_node(tools_dict: Dict[str, Any]):
    """Creates the tool execution node with state auditing for the Merchant Agent."""
    async def tools_node(state: AgentState):
        last_message = state["messages"][-1]
        tool_messages = []
        updates: Dict[str, Any] = {}

        last_tool_name = None
        last_tool_args = None
        last_tool_parsed = None
        analytics_ctx = state.get("analytics_context")

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call.get("args") or {})

            # Guarantee merchant authorization on tool call
            if "caller_role" not in tool_args:
                tool_args["caller_role"] = "merchant"

            tool = tools_dict.get(tool_name)
            if tool is None:
                err_msg = json.dumps({"error": f"Tool '{tool_name}' is not recognized."})
                tool_messages.append(ToolMessage(content=err_msg, tool_call_id=tool_call["id"]))
                continue

            try:
                raw_res = await tool.ainvoke(tool_args)
            except Exception as e:
                logger.exception("[MERCHANT TOOL ERROR] Tool '%s' execution failed: %s", tool_name, e)
                err_content = json.dumps({"status": "error", "error": str(e)})
                tool_messages.append(ToolMessage(content=err_content, tool_call_id=tool_call["id"]))
                continue

            res_text = _extract_text(raw_res)
            parsed_dict = _safe_parse(res_text)

            # Record state tracking metadata
            last_tool_name = tool_name
            last_tool_args = tool_args
            last_tool_parsed = parsed_dict or {"raw": res_text[:300]}

            # Cache analytics if analytics was queried
            if "analytics" in tool_name and parsed_dict and parsed_dict.get("status") == "success":
                analytics_ctx = parsed_dict

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=tool_call["id"]))

        updates["messages"] = tool_messages
        if last_tool_name:
            updates["last_tool_called"] = last_tool_name
            updates["last_tool_args"] = last_tool_args
            updates["last_tool_result"] = last_tool_parsed
        if analytics_ctx:
            updates["analytics_context"] = analytics_ctx

        return updates

    return tools_node
