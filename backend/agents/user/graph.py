import os
import re
import json
import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from agents.user.state import AgentState
from agents.user.director import DirectorAgent
from agents.user.general import GeneralAgent
from agents.user.checkpointer import checkPointer
from utils.text_cleaning import clean_ai_output


# --- Tool Helpers ---

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


def _extract_state_updates_from_tool_result(tool_name: str, parsed: dict) -> dict:
    """Extracts structured values from tool response dictionary and maps them to AgentState fields."""
    if not isinstance(parsed, dict):
        return {}

    updates = {}

    # 1. Product Recommendations & Discovery
    if "products" in parsed:
        updates["suggested_products"] = parsed.get("products", [])
    elif "suggested_products" in parsed:
        updates["suggested_products"] = parsed.get("suggested_products", [])

    # 2. Pricing, Bargaining & Discounts
    if "next_discount_percent" in parsed and parsed.get("next_discount_percent") is not None:
        updates["current_discount_percent"] = float(parsed["next_discount_percent"])
    elif "counter_offer_discount_percent" in parsed and parsed.get("counter_offer_discount_percent") is not None:
        updates["current_discount_percent"] = float(parsed["counter_offer_discount_percent"])
    elif "counter_offer_percent" in parsed and parsed.get("counter_offer_percent") is not None:
        updates["current_discount_percent"] = float(parsed["counter_offer_percent"])
    elif "current_discount_percent" in parsed and parsed.get("current_discount_percent") is not None:
        updates["current_discount_percent"] = float(parsed["current_discount_percent"])

    if "combo_offer" in parsed:
        updates["combo_offer"] = parsed.get("combo_offer")

    if "counter_offer_price" in parsed and parsed.get("counter_offer_price") is not None:
        updates["cart_total"] = float(parsed["counter_offer_price"])

    # 3. Cart & Shopping Bag
    if "items" in parsed:
        updates["cart"] = parsed.get("items", [])
        updates["cart_items"] = parsed.get("items", [])
    if "total_amount" in parsed and parsed.get("total_amount") is not None:
        updates["cart_total"] = float(parsed["total_amount"])
    if "subtotal" in parsed and parsed.get("subtotal") is not None:
        updates["cart_subtotal"] = float(parsed["subtotal"])
    if "count" in parsed and parsed.get("count") is not None:
        updates["cart_count"] = int(parsed["count"])

    if tool_name == "clear_cart" and parsed.get("success"):
        updates["cart"] = []
        updates["cart_items"] = []
        updates["cart_total"] = 0.0
        updates["cart_subtotal"] = 0.0
        updates["cart_count"] = 0

    # 4. Payments & Checkout Links
    if "pending_payment_link" in parsed:
        updates["pending_payment_link"] = parsed.get("pending_payment_link")
    elif "payment_link" in parsed:
        updates["pending_payment_link"] = parsed.get("payment_link")

    if "pending_payment_link_id" in parsed:
        updates["pending_payment_link_id"] = parsed.get("pending_payment_link_id")
    elif "payment_link_id" in parsed:
        updates["pending_payment_link_id"] = parsed.get("payment_link_id")

    return updates


# --- Post Processing & Routing Functions ---

def post_process_node(state: AgentState):
    """Formats final response and strips reasoning thought tags."""
    messages = state.get("messages", [])
    if not messages:
        return {}

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

    return {"final_response": final_text}


def route_from_director(state: AgentState):
    """Routes from Director classification directly to the target specialist agent."""
    intent = state.get("intent", "general")
    if intent in ("product", "product_search", "recommendation"):
        return "recommendation"
    if intent in ("cart", "cart_editing"):
        return "cart"
    if intent in ("pricing", "negotiation", "pricing_negotiation"):
        return "negotiation"
    return "general"


def route_specialist(state: AgentState):
    """Routes specialist response to tool execution if tool_calls are present; otherwise to post_process."""
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        return "tools"
    return "post_process"


# --- Tools Node Creation ---

def create_tools_node(tools_dict=None):
    """
    Creates a dual sync/async tools execution node for the user agent graph.
    Resolves tools from MCP tools_dict and local feature modules (Cart, Negotiation, Recommedation),
    executes tool calls, and propagates structured output back to AgentState.
    """
    resolved_tools = {}
    if tools_dict:
        if isinstance(tools_dict, dict):
            resolved_tools.update(tools_dict)
        elif isinstance(tools_dict, list):
            for t in tools_dict:
                name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
                resolved_tools[name] = t

    # Ensure local feature tool suites are available
    for module_name, getter_name in [
        ("Cart.tools", "get_cart_langchain_tools"),
        ("Negotiation.tools", "get_negotiation_langchain_tools"),
        ("Recommedation.tools", "get_recommendation_langchain_tools"),
    ]:
        try:
            mod = __import__(module_name, fromlist=[getter_name])
            getter = getattr(mod, getter_name)
            for t in getter():
                name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
                if name and name not in resolved_tools:
                    resolved_tools[name] = t
        except Exception:
            pass

    def _sync_execute_tools(state: AgentState):
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {}

        tool_messages = []
        updates = {}

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = dict(tool_call.get("args") or {})
            call_id = tool_call.get("id")

            tool = resolved_tools.get(tool_name)
            if tool is None:
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps({"error": f"Unknown tool '{tool_name}'"}),
                        tool_call_id=call_id,
                    )
                )
                continue

            accepted_params = getattr(tool, "args", {}) or {}
            if "user_id" in accepted_params:
                tool_args["user_id"] = tool_args.get("user_id") or state.get("user_id", 0)
            if "thread_id" in accepted_params:
                tool_args["thread_id"] = tool_args.get(
                    "thread_id", state.get("thread_id", str(state.get("user_id", 0)))
                )
            if "current_discount_percent" in accepted_params and "current_discount_percent" not in tool_args:
                tool_args["current_discount_percent"] = state.get("current_discount_percent", 0.0)
            if "gender" in accepted_params and "gender" not in tool_args and state.get("gender"):
                tool_args["gender"] = state.get("gender")

            try:
                if hasattr(tool, "invoke"):
                    raw_res = tool.invoke(tool_args)
                elif hasattr(tool, "ainvoke"):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as pool:
                                raw_res = pool.submit(asyncio.run, tool.ainvoke(tool_args)).result()
                        else:
                            raw_res = loop.run_until_complete(tool.ainvoke(tool_args))
                    except Exception:
                        raw_res = asyncio.run(tool.ainvoke(tool_args))
                elif callable(tool):
                    try:
                        raw_res = tool(**tool_args)
                    except TypeError:
                        raw_res = tool(tool_args)
                else:
                    raw_res = tool
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps({"error": str(e)}),
                        tool_call_id=call_id,
                    )
                )
                continue

            res_text = _extract_text(raw_res)
            parsed = _safe_parse(res_text)

            if isinstance(parsed, dict):
                state_updates = _extract_state_updates_from_tool_result(tool_name, parsed)
                updates.update(state_updates)

                # If a cart modifying tool ran, refresh cart summary from DB if user_id > 0
                if tool_name in ("add_to_cart", "update_cart_quantity", "remove_from_cart") and parsed.get("success"):
                    effective_uid = tool_args.get("user_id") or state.get("user_id", 0)
                    if effective_uid and effective_uid > 0:
                        try:
                            from Cart.controller import cartController
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        summary = pool.submit(asyncio.run, cartController.get_summary(user_id=effective_uid)).result()
                                else:
                                    summary = loop.run_until_complete(cartController.get_summary(user_id=effective_uid))
                            except Exception:
                                summary = asyncio.run(cartController.get_summary(user_id=effective_uid))
                            if summary and summary.get("success"):
                                updates["cart"] = summary.get("items", [])
                                updates["cart_items"] = summary.get("items", [])
                                updates["cart_total"] = summary.get("total_amount", 0.0)
                                updates["cart_subtotal"] = summary.get("subtotal", 0.0)
                        except Exception:
                            pass

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=call_id))

        updates["messages"] = tool_messages
        return updates

    async def _async_execute_tools(state: AgentState):
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {}

        tool_messages = []
        updates = {}

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = dict(tool_call.get("args") or {})
            call_id = tool_call.get("id")

            tool = resolved_tools.get(tool_name)
            if tool is None:
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps({"error": f"Unknown tool '{tool_name}'"}),
                        tool_call_id=call_id,
                    )
                )
                continue

            accepted_params = getattr(tool, "args", {}) or {}
            if "user_id" in accepted_params:
                tool_args["user_id"] = tool_args.get("user_id") or state.get("user_id", 0)
            if "thread_id" in accepted_params:
                tool_args["thread_id"] = tool_args.get(
                    "thread_id", state.get("thread_id", str(state.get("user_id", 0)))
                )
            if "current_discount_percent" in accepted_params and "current_discount_percent" not in tool_args:
                tool_args["current_discount_percent"] = state.get("current_discount_percent", 0.0)
            if "gender" in accepted_params and "gender" not in tool_args and state.get("gender"):
                tool_args["gender"] = state.get("gender")

            try:
                if hasattr(tool, "ainvoke"):
                    raw_res = await tool.ainvoke(tool_args)
                elif hasattr(tool, "invoke"):
                    raw_res = await asyncio.to_thread(tool.invoke, tool_args)
                elif callable(tool):
                    try:
                        raw_res = await asyncio.to_thread(tool, **tool_args)
                    except TypeError:
                        raw_res = await asyncio.to_thread(tool, tool_args)
                else:
                    raw_res = tool
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps({"error": str(e)}),
                        tool_call_id=call_id,
                    )
                )
                continue

            res_text = _extract_text(raw_res)
            parsed = _safe_parse(res_text)

            if isinstance(parsed, dict):
                state_updates = _extract_state_updates_from_tool_result(tool_name, parsed)
                updates.update(state_updates)

                # If a cart modifying tool ran, refresh cart summary from DB if user_id > 0
                if tool_name in ("add_to_cart", "update_cart_quantity", "remove_from_cart") and parsed.get("success"):
                    effective_uid = tool_args.get("user_id") or state.get("user_id", 0)
                    if effective_uid and effective_uid > 0:
                        try:
                            from Cart.controller import cartController
                            summary = await cartController.get_summary(user_id=effective_uid)
                            if summary and summary.get("success"):
                                updates["cart"] = summary.get("items", [])
                                updates["cart_items"] = summary.get("items", [])
                                updates["cart_total"] = summary.get("total_amount", 0.0)
                                updates["cart_subtotal"] = summary.get("subtotal", 0.0)
                        except Exception:
                            pass

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=call_id))

        updates["messages"] = tool_messages
        return updates

    return RunnableLambda(_sync_execute_tools, afunc=_async_execute_tools)


# --- Graph Assembly ---

def initialize_agents(fast_llm, medium_llm, small_llm, tools_dict):
    """Initializes and returns all specialist agents and the tools node."""
    from Cart.agent import CartAgent
    from Negotiation.agent import NegotiationAgent
    from Recommedation.agent import RecommendationAgent

    agents = {
        "director": DirectorAgent(small_llm),
        "recommendation": RecommendationAgent(fast_llm),
        "cart": CartAgent(fast_llm),
        "negotiation": NegotiationAgent(fast_llm),
        "general": GeneralAgent(small_llm, tools=[]),
    }

    tools_node = create_tools_node(tools_dict)
    return agents, tools_node


def setup_nodes(workflow: StateGraph, agents: dict, tools_node):
    """Registers all workflow nodes to the StateGraph."""
    workflow.add_node("director", agents["director"].run)
    workflow.add_node("recommendation", agents["recommendation"].run)
    workflow.add_node("cart", agents["cart"].run)
    workflow.add_node("negotiation", agents["negotiation"].run)
    workflow.add_node("general", agents["general"].run)
    workflow.add_node("tools", tools_node)
    workflow.add_node("post_process", post_process_node)


def setup_edges(workflow: StateGraph):
    """
    Registers edges and routing logic:
    1. Director routes to the chosen specialist.
    2. Specialist routes to 'tools' if tool_calls exist, else 'post_process'.
    3. When tools finish, they route BACK TO DIRECTOR to handle any follow-up intent (adding to cart, negotiation, etc.).
    4. PostProcess routes to END.
    """
    workflow.set_entry_point("director")

    # 1. Route from Director
    workflow.add_conditional_edges(
        "director",
        route_from_director,
        {
            "recommendation": "recommendation",
            "cart": "cart",
            "negotiation": "negotiation",
            "general": "general",
        },
    )

    # 2. Route from Specialists to tools (if tool calls) or post_process (if complete)
    specialist_nodes = ["recommendation", "cart", "negotiation", "general"]
    for node in specialist_nodes:
        workflow.add_conditional_edges(
            node,
            route_specialist,
            {"tools": "tools", "post_process": "post_process"},
        )

    # 3. When tools return results, re-evaluate through Director
    workflow.add_edge("tools", "director")

    # 4. Final step
    workflow.add_edge("post_process", END)


def compile_agent_graph(fast_llm, medium_llm, small_llm, tools_dict):
    """Main orchestrator function that compiles the entire user agent graph."""
    workflow = StateGraph(AgentState)
    agents, tools_node = initialize_agents(fast_llm, medium_llm, small_llm, tools_dict)

    setup_nodes(workflow, agents, tools_node)
    setup_edges(workflow)

    checkpointer_instance = checkPointer.getCheckPointer(prefer="redis")
    return workflow.compile(checkpointer=checkpointer_instance)
