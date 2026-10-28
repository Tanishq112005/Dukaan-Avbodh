import os
import json
import uuid
import asyncio
import logging
from typing import Any, Optional, Dict, List, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from agents.merchant.state import AgentState
from agents.merchant.agent import MerchantAgent
from agents.merchant.checkpointer import checkPointer
from utils.text_cleaning import clean_ai_output

logger = logging.getLogger(__name__)

# --- Tool Categories for Merchant Generative UI Scoping ---
ANALYTICS_TOOLS = {
    "merchant_get_store_analytics",
}

TOP_SELLING_TOOLS = {
    "merchant_get_top_selling_products",
}

INVENTORY_TOOLS = {
    "merchant_get_inventory_health_and_reorder_alerts",
}

ORDER_TOOLS = {
    "merchant_lookup_order_details",
}

PRICING_TOOLS = {
    "merchant_update_product_pricing_and_margin",
}

NEGOTIATION_INSIGHTS_TOOLS = {
    "merchant_get_customer_negotiation_insights",
}

CATALOG_TOOLS = {
    "merchant_publish_catalog_item",
    "merchant_add_product",
}

PRODUCT_EDIT_TOOLS = {
    "merchant_edit_product_details",
    "merchant_update_product_details",
}

PRODUCT_INSPECT_TOOLS = {
    "merchant_get_product_details",
}

PRODUCT_DELETE_TOOLS = {
    "merchant_delete_product",
}


def _extract_text(res: Any) -> str:
    """Extracts a string representation from a tool execution result."""
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


def _extract_state_updates_from_tool_result(tool_name: str, parsed: dict) -> dict:
    """Extracts structured values from tool response dictionary and maps them to AgentState fields."""
    if not isinstance(parsed, dict):
        return {}

    updates: Dict[str, Any] = {}

    if tool_name in ANALYTICS_TOOLS and parsed.get("status") == "success":
        updates["analytics_context"] = parsed

    elif tool_name in TOP_SELLING_TOOLS and parsed.get("status") == "success":
        updates["top_selling_products"] = parsed.get("top_products", [])

    elif tool_name in INVENTORY_TOOLS and parsed.get("status") == "success":
        updates["inventory_alerts"] = parsed.get("critical_items", [])

    elif tool_name in ORDER_TOOLS and parsed.get("status") == "success":
        updates["order_lookup"] = parsed.get("order")

    elif tool_name in PRICING_TOOLS and parsed.get("status") == "success":
        updates["pricing_updates"] = parsed

    elif tool_name in NEGOTIATION_INSIGHTS_TOOLS and parsed.get("status") == "success":
        updates["negotiation_insights"] = parsed.get("negotiation_metrics")

    elif tool_name in PRODUCT_EDIT_TOOLS and parsed.get("status") == "success":
        updates["pricing_updates"] = parsed

    elif tool_name in PRODUCT_INSPECT_TOOLS and parsed.get("status") == "success":
        updates["order_lookup"] = parsed.get("product")

    return updates


def deduplicate_cards(raw_cards: List[dict]) -> List[dict]:
    """Retains the latest active card per card type, preventing outdated duplicates in the UI."""
    if not raw_cards:
        return []

    card_map = {}
    for card in raw_cards:
        if not isinstance(card, dict) or not card.get("type"):
            continue
        c_type = card.get("type")
        c_data = card.get("data") or {}
        prod_id = c_data.get("product_id") or c_data.get("id")

        if prod_id:
            key = f"{c_type}_{prod_id}"
        else:
            key = c_type

        card_map[key] = card

    return list(card_map.values())


def _build_cards_from_tool(tool_name: str, parsed: dict, updates: dict, state: Optional[dict] = None) -> List[dict]:
    """Generates structured Generative UI card descriptors for the merchant dashboard."""
    cards = []
    suffix = uuid.uuid4().hex[:6]

    if tool_name in ANALYTICS_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"analytics_{suffix}",
            "type": "merchant_analytics",
            "data": {
                "title": "Store Performance Snapshot",
                "time_range": parsed.get("time_range", "all"),
                "gross_revenue_inr": parsed.get("gross_revenue_inr", 0.0),
                "net_profit_inr": parsed.get("net_profit_inr", 0.0),
                "profit_margin_percent": parsed.get("profit_margin_percent", 0.0),
                "total_orders_count": parsed.get("total_orders_count", 0),
                "total_items_sold": parsed.get("total_items_sold", 0),
                "average_order_value_inr": parsed.get("average_order_value_inr", 0.0),
                "total_discounts_granted_inr": parsed.get("total_discounts_granted_inr", 0.0),
                "average_discount_percent": parsed.get("average_discount_percent", 0.0),
                "active_customers_count": parsed.get("active_customers_count", 0),
            },
        })

    elif tool_name in TOP_SELLING_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"top_products_{suffix}",
            "type": "merchant_top_products",
            "data": {
                "title": "Top Selling Products",
                "count": parsed.get("count", 0),
                "products": parsed.get("top_products", []),
            },
        })

    elif tool_name in INVENTORY_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"inventory_{suffix}",
            "type": "merchant_inventory_alerts",
            "data": {
                "title": "Inventory Health & Stock Alerts",
                "threshold": parsed.get("threshold", 10),
                "out_of_stock_count": parsed.get("out_of_stock_count", 0),
                "low_stock_count": parsed.get("low_stock_count", 0),
                "critical_items": parsed.get("critical_items", []),
            },
        })

    elif tool_name in ORDER_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"order_{suffix}",
            "type": "merchant_order_details",
            "data": {
                "title": f"Order #{parsed.get('order', {}).get('id', 'Details')}",
                "order": parsed.get("order"),
            },
        })

    elif tool_name in PRICING_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"pricing_{suffix}",
            "type": "merchant_pricing_update",
            "data": {
                "title": "Pricing & Margin Floor Updated",
                "product_id": parsed.get("product_id"),
                "name": parsed.get("name"),
                "old_price": parsed.get("old_price"),
                "new_price": parsed.get("new_price"),
                "cost_price": parsed.get("cost_price"),
                "min_profit_margin_percent": parsed.get("min_profit_margin_percent"),
                "message": parsed.get("message"),
            },
        })

    elif tool_name in NEGOTIATION_INSIGHTS_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"negotiation_insights_{suffix}",
            "type": "merchant_negotiation_insights",
            "data": {
                "title": "Buyer Negotiation Insights & Funnel",
                "metrics": parsed.get("negotiation_metrics", {}),
            },
        })

    elif tool_name in CATALOG_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"publish_{suffix}",
            "type": "merchant_product_published",
            "data": {
                "title": "Product Published to Catalog",
                "product_id": parsed.get("product_id"),
                "message": parsed.get("message"),
                "details": parsed.get("data"),
            },
        })

    elif tool_name in PRODUCT_EDIT_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"product_edit_{suffix}",
            "type": "merchant_product_updated",
            "data": {
                "title": f"Product #{parsed.get('product_id')} Updated",
                "product_id": parsed.get("product_id"),
                "message": parsed.get("message"),
                "updated_fields": parsed.get("updated_fields", []),
                "details": parsed.get("data"),
            },
        })

    elif tool_name in PRODUCT_INSPECT_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"product_detail_{suffix}",
            "type": "merchant_product_details",
            "data": {
                "title": f"Product #{parsed.get('product_id')} Overview",
                "product_id": parsed.get("product_id"),
                "product": parsed.get("product"),
            },
        })

    elif tool_name in PRODUCT_DELETE_TOOLS and parsed.get("status") == "success":
        cards.append({
            "id": f"product_del_{suffix}",
            "type": "merchant_product_deleted",
            "data": {
                "title": f"Product #{parsed.get('product_id')} Removed",
                "product_id": parsed.get("product_id"),
                "message": parsed.get("message"),
            },
        })

    return cards


def post_process_node(state: AgentState) -> dict:
    """Extracts final sanitized assistant text and deduplicated Generative UI cards."""
    messages = state.get("messages", [])
    if not messages:
        return {"final_response": "", "cards": []}

    final_text = ""
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", "")
        content = getattr(msg, "content", "")
        has_tool_calls = bool(getattr(msg, "tool_calls", None))

        if (msg_type == "ai" or hasattr(msg, "tool_calls")) and not has_tool_calls and content:
            if isinstance(content, list):
                final_text = "\n".join(
                    [
                        str(x) if isinstance(x, str) else x.get("text", "")
                        for x in content
                        if isinstance(x, (str, dict))
                    ]
                )
            else:
                final_text = str(content)
            break

    if not final_text:
        last_msg = messages[-1]
        raw = getattr(last_msg, "content", "")
        if isinstance(raw, list):
            final_text = "\n".join(
                [
                    str(x) if isinstance(x, str) else x.get("text", "")
                    for x in raw
                    if isinstance(x, (str, dict))
                ]
            )
        else:
            final_text = str(raw)

    if final_text:
        final_text = clean_ai_output(final_text)

    cards = deduplicate_cards(list(state.get("cards") or []))
    return {"final_response": final_text, "cards": cards}


def route_agent(state: AgentState):
    """Routes agent response to tool execution if tool_calls exist; otherwise to post_process."""
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        return "tools"
    return "post_process"


def resolve_all_merchant_tools(tools_dict=None) -> Dict[str, Any]:
    """Resolves and returns all 7 native merchant tools wrapped in a dict mapping name -> tool."""
    resolved = {}
    if tools_dict:
        if isinstance(tools_dict, dict):
            resolved.update(tools_dict)
        elif isinstance(tools_dict, list):
            for t in tools_dict:
                name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
                if name:
                    resolved[name] = t

    try:
        from Merchant.tools import get_merchant_langchain_tools
        native_tools = get_merchant_langchain_tools()
        for t in native_tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
            if name and name not in resolved:
                resolved[name] = t
    except Exception as e:
        logger.warning("Could not auto-resolve merchant langchain tools: %s", e)

    return resolved


def _log_tool_audit(tool_name: str, tool_args: dict, parsed: Any, state: dict):
    """Logs tool actions and security bounds into dukaan_audit.audit_logs."""
    try:
        from services.audit_logger import audit_logger
        merchant_id = tool_args.get("merchant_id") or state.get("merchant_id") or state.get("user_id", 1)
        asyncio.create_task(
            audit_logger.log_event(
                event_type=f"merchant_tool_{tool_name}",
                user_id=merchant_id,
                details={
                    "tool": tool_name,
                    "args": tool_args,
                    "status": parsed.get("status") if isinstance(parsed, dict) else "executed",
                },
            )
        )
    except Exception:
        pass


def create_tools_node(resolved_tools: Dict[str, Any]):
    """Creates the tool execution node with parallel concurrency and state auditing."""
    async def _async_execute_tools(state: AgentState) -> dict:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {}

        tool_messages = []
        updates: Dict[str, Any] = {}
        cards = []

        last_tool_name = None
        last_tool_args = None
        last_tool_parsed = None

        async def _execute_single_tool(tool_call):
            tool_name = tool_call.get("name")
            tool_args = dict(tool_call.get("args") or {})
            call_id = tool_call.get("id")

            # Guarantee merchant authorization
            if "caller_role" not in tool_args:
                tool_args["caller_role"] = "merchant"

            tool = resolved_tools.get(tool_name)
            if tool is None:
                err_res = json.dumps({"error": f"Tool '{tool_name}' is not recognized."})
                return tool_name, call_id, tool_args, err_res

            try:
                if hasattr(tool, "ainvoke"):
                    raw_res = await tool.ainvoke(tool_args)
                elif hasattr(tool, "invoke"):
                    raw_res = await asyncio.to_thread(tool.invoke, tool_args)
                elif callable(tool):
                    raw_res = await asyncio.to_thread(tool, **tool_args)
                else:
                    raw_res = tool
                res_text = _extract_text(raw_res)
            except Exception as e:
                logger.exception("[MERCHANT TOOL ERROR] Tool '%s' failed: %s", tool_name, e)
                res_text = json.dumps({"status": "error", "error": str(e)})

            return tool_name, call_id, tool_args, res_text

        results = await asyncio.gather(*[_execute_single_tool(tc) for tc in tool_calls])

        for tool_name, call_id, tool_args, res_text in results:
            parsed = _safe_parse(res_text)
            if isinstance(parsed, dict):
                state_updates = _extract_state_updates_from_tool_result(tool_name, parsed)
                updates.update(state_updates)

                new_cards = _build_cards_from_tool(tool_name, parsed, state_updates, state)
                if new_cards:
                    cards.extend(new_cards)

                last_tool_name = tool_name
                last_tool_args = tool_args
                last_tool_parsed = parsed
                _log_tool_audit(tool_name, tool_args, parsed, state)

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=call_id))

        if last_tool_name:
            updates["last_tool_called"] = last_tool_name
            updates["last_tool_args"] = last_tool_args
            updates["last_tool_result"] = last_tool_parsed

        updates["cards"] = deduplicate_cards(cards)
        updates["messages"] = tool_messages
        return updates

    def _sync_execute_tools(state: AgentState) -> dict:
        return asyncio.run(_async_execute_tools(state))

    return RunnableLambda(_sync_execute_tools, afunc=_async_execute_tools)


def initialize_agents(fast_llm, tools_dict=None):
    """Initializes the unified MerchantAgent and tools node with all domain tools."""
    resolved_tools = resolve_all_merchant_tools(tools_dict)
    tools_list = list(resolved_tools.values())

    merchant_agent = MerchantAgent(fast_llm, tools=tools_list)
    tools_node = create_tools_node(resolved_tools)

    agents = {"agent": merchant_agent}
    return agents, tools_node


def setup_nodes(workflow: StateGraph, agents: dict, tools_node):
    """Registers workflow nodes to the StateGraph."""
    agent_node = RunnableLambda(agents["agent"].run, afunc=agents["agent"].arun)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("post_process", post_process_node)


def setup_edges(workflow: StateGraph):
    """
    Registers routing edges for the unified merchant agent:
      1. 'agent' is the entry point.
      2. 'agent' routes to 'tools' if tool calls are present; otherwise to 'post_process'.
      3. 'tools' routes back to 'agent' to synthesize live metrics into executive commentary.
      4. 'post_process' routes to END.
    """
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        route_agent,
        {
            "tools": "tools",
            "post_process": "post_process",
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("post_process", END)


def compile_agent_graph(fast_llm, tools_dict=None):
    """Compiles the StateGraph into an executable LangGraph instance with checkpointer."""
    workflow = StateGraph(AgentState)
    agents, tools_node = initialize_agents(fast_llm, tools_dict)

    setup_nodes(workflow, agents, tools_node)
    setup_edges(workflow)

    checkpointer_instance = checkPointer.getCheckPointer(prefer="memory")
    return workflow.compile(checkpointer=checkpointer_instance)
