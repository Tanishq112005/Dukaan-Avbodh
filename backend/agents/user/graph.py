import os
import re
import json
import uuid
import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from agents.user.state import AgentState
from agents.user.agent import UserAgent
from agents.user.checkpointer import checkPointer
from utils.text_cleaning import clean_ai_output


# --- Tool Categories for Strict UI Scoping ---

RECOMMENDATION_TOOLS = {
    "search_and_recommend_by_type",
    "recommend_by_query",
    "get_personalized_recommendations",
    "get_category_best_sellers",
    "get_global_best_sellers",
    "search_catalog",
    "recommend_products",
}

CART_VIEW_TOOLS = {
    "get_cart_items",
    "get_cart_summary",
}

CART_MUTATION_TOOLS = {
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "clear_cart",
}

NEGOTIATION_TOOLS = {
    "negotiate_discount",
    "evaluate_counter_offer",
}

PAYMENT_TOOLS = {
    "create_payment_order",
}

ORDER_CREATION_TOOLS = {
    "checkout_order",
    "create_order",
    "create_payment_order",
}

ORDER_TRACKING_TOOLS = {
    "track_order",
    "get_order_status",
}

ORDER_LISTING_TOOLS = {
    "get_my_orders",
    "get_user_orders",
}

ORDER_MUTATION_TOOLS = {
    "cancel_order",
}

ORDER_STATUS_TOOLS = {
    "check_order_payment_status",
    "check_payment_status",
    "verify_order_payment",
}

AUTH_TOOLS = {
    "get_user_profile",
    "update_user_profile",
    "check_auth_status",
    "request_login",
}


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

    # 1. Product Recommendations & Discovery (strictly for recommendation tools)
    if tool_name in RECOMMENDATION_TOOLS:
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

    # 4. Payments, Checkout Links & Orders
    if "pending_payment_link" in parsed:
        updates["pending_payment_link"] = parsed.get("pending_payment_link")
    elif "payment_link" in parsed:
        updates["pending_payment_link"] = parsed.get("payment_link")

    if "pending_payment_link_id" in parsed:
        updates["pending_payment_link_id"] = parsed.get("pending_payment_link_id")
    elif "payment_link_id" in parsed:
        updates["pending_payment_link_id"] = parsed.get("payment_link_id")

    if "order_ids" in parsed and parsed.get("order_ids"):
        updates["order_ids"] = parsed.get("order_ids")
        updates["order_placed"] = True

    if (tool_name in ORDER_STATUS_TOOLS or tool_name in ORDER_CREATION_TOOLS) and parsed.get("paid"):
        updates["payment_confirmed"] = True
        updates["cart"] = []
        updates["cart_items"] = []
        updates["cart_total"] = 0.0
        updates["cart_subtotal"] = 0.0
        updates["cart_count"] = 0

    # 5. Customer Profile & Identity
    if tool_name in AUTH_TOOLS:
        if "user_id" in parsed and parsed.get("user_id"):
            updates["user_id"] = int(parsed["user_id"])
        if "name" in parsed or "address" in parsed or "email" in parsed:
            updates["customer_profile"] = {
                "name": parsed.get("name"),
                "email": parsed.get("email"),
                "address": parsed.get("address"),
            }

    return updates


def _build_cards_from_tool(tool_name: str, parsed: dict, updates: dict, state: dict = None) -> list:
    """
    Builds frontend Generative UI card descriptors strictly based on the executed tool:
    - Recommendations ONLY when a discovery/recommendation tool runs.
    - Cart items ONLY when cart view or mutation tools run.
    - Negotiation offer ONLY when price negotiation tools run.
    - Payment/ordering card ONLY when checkout tool runs, displaying photos of the items being ordered.
    - Order tracking card ONLY when order tracking tools run.
    - Order confirmed card ONLY when payment completes.
    """
    cards = []
    suffix = uuid.uuid4().hex[:6]

    # 1. Product Recommendations Card: ONLY when an actual recommendation tool executed
    if tool_name in RECOMMENDATION_TOOLS:
        suggested = updates.get("suggested_products") or parsed.get("products") or parsed.get("suggested_products")
        if suggested and isinstance(suggested, list) and len(suggested) > 0:
            normalized_prods = []
            for p in suggested:
                if isinstance(p, dict) and "product" in p and isinstance(p["product"], dict):
                    info = dict(p["product"])
                    if "id" not in info and "product_id" in p:
                        info["id"] = p["product_id"]
                    normalized_prods.append(info)
                elif isinstance(p, dict):
                    normalized_prods.append(p)
            if normalized_prods:
                cards.append({
                    "id": f"rec_{suffix}",
                    "type": "recommendation",
                    "data": {
                        "title": "Curated Stylist Picks",
                        "products": normalized_prods,
                        "count": len(normalized_prods),
                    },
                })

    # 2. Cart Items View Card: when user asks "show me products in the cart" or cart inspection tools run
    elif tool_name in CART_VIEW_TOOLS:
        cart_items = updates.get("cart") or parsed.get("items") or (state.get("cart") if state else [])
        cards.append({
            "id": f"cart_{suffix}",
            "type": "cart_update",
            "data": {
                "title": "Your Shopping Bag",
                "action": "view",
                "cart": cart_items or [],
                "cart_total": updates.get("cart_total") or parsed.get("total_amount") or (state.get("cart_total") if state else None),
                "cart_count": updates.get("cart_count") or (len(cart_items) if cart_items else 0),
            },
        })

    # 3. Cart Mutation Card: when items are added, updated, or removed from the cart
    elif tool_name in CART_MUTATION_TOOLS and parsed.get("success"):
        action = (
            "cleared" if tool_name == "clear_cart"
            else "added" if "add" in tool_name
            else "removed" if ("remove" in tool_name or (tool_name == "update_cart_quantity" and parsed.get("quantity") == 0))
            else "updated"
        )
        item_data = parsed.get("item") or parsed.get("added_item")
        if not item_data and "name" in parsed:
            item_data = {
                "name": parsed.get("name"),
                "price": parsed.get("price"),
                "size": parsed.get("size"),
                "qty": parsed.get("quantity", 1),
                "image_url": parsed.get("image_url"),
            }
        cards.append({
            "id": f"cart_{suffix}",
            "type": "cart_update",
            "data": {
                "title": "Shopping Bag Updated",
                "action": action,
                "item": item_data,
                "cart_total": updates.get("cart_total"),
                "cart_subtotal": updates.get("cart_subtotal"),
                "cart_count": updates.get("cart_count"),
                "cart": updates.get("cart"),
            },
        })

    # 4. Price Bargaining & Negotiation Card: ONLY when negotiation tool runs
    elif tool_name in NEGOTIATION_TOOLS:
        discount_val = (
            updates.get("current_discount_percent")
            or parsed.get("counter_offer_discount_percent")
            or parsed.get("next_discount_percent")
            or 0.0
        )
        offer_price = parsed.get("counter_offer_price") or parsed.get("discounted_price") or updates.get("cart_total")
        original_price = parsed.get("subtotal") or parsed.get("original_subtotal") or updates.get("cart_subtotal")
        savings = parsed.get("savings")
        if not savings and original_price and offer_price and original_price > offer_price:
            savings = round(float(original_price) - float(offer_price), 2)

        cards.append({
            "id": f"neg_{suffix}",
            "type": "negotiation",
            "data": {
                "title": "VIP Price Offer",
                "discount_percent": float(discount_val),
                "original_price": original_price,
                "offer_price": offer_price,
                "savings": savings,
                "combo_offer": updates.get("combo_offer") or parsed.get("combo_offer"),
                "status": "active",
            },
        })

    # 5. Instant Payment Card during Checkout: displays photos of the items being ordered from cart
    elif tool_name in PAYMENT_TOOLS or tool_name in ORDER_CREATION_TOOLS:
        link = updates.get("pending_payment_link") or parsed.get("payment_link")
        if link:
            ordered_cart = parsed.get("ordered_items") or updates.get("cart") or (state.get("cart") if state else [])
            cards.append({
                "id": f"pay_{suffix}",
                "type": "payment",
                "data": {
                    "title": "Instant Secure Checkout",
                    "payment_link": link,
                    "payment_link_id": updates.get("pending_payment_link_id") or parsed.get("payment_link_id"),
                    "amount": parsed.get("total_amount") or parsed.get("amount") or updates.get("cart_total"),
                    "cart": ordered_cart,
                    "order_ids": parsed.get("order_ids") or updates.get("order_ids"),
                    "currency": "INR",
                    "status": "ready",
                },
            })

    # 6. Live Order Tracking Card: when user asks "track my order" or order tracking tool runs
    elif tool_name in ORDER_TRACKING_TOOLS and parsed.get("success"):
        cards.append({
            "id": f"track_{suffix}",
            "type": "order_tracking",
            "data": {
                "title": "Live Order Tracking",
                "order_id": str(parsed.get("order_id") or "ORD-2026"),
                "status": parsed.get("status") or "placed",
                "stage": parsed.get("stage") or "Order Placed",
                "delivery_estimate": parsed.get("delivery_estimate") or "3-5 Business Days",
                "amount": parsed.get("amount"),
                "items": parsed.get("items") or [],
            },
        })

    # 7. Order Confirmed Card: when payment completed or confirmed
    elif tool_name in ORDER_STATUS_TOOLS or updates.get("payment_confirmed") or parsed.get("paid"):
        cards.append({
            "id": f"ord_{suffix}",
            "type": "order_confirmed",
            "data": {
                "title": "Order Placed Successfully",
                "paid": True,
                "order_id": parsed.get("order_id") or parsed.get("razorpay_payment_id") or parsed.get("payment_id") or "CONFIRMED",
                "amount": parsed.get("amount") or parsed.get("total_amount"),
                "delivery_estimate": "3-5 Business Days",
                "status": "confirmed",
            },
        })

    return cards


# --- Post Processing & Routing Functions ---

def post_process_node(state: AgentState):
    """
    Formats final response and cleans thought tags.
    Returns ONLY the cards produced during the current turn (no stale cross-turn synthesis).
    """
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

    # Return only the cards generated in this turn
    cards = list(state.get("cards") or [])
    return {"final_response": final_text, "cards": cards}


def route_agent(state: AgentState):
    """Routes agent response to tool execution if tool_calls are present; otherwise to post_process."""
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        return "tools"
    return "post_process"


# Backward-compatible alias
route_specialist = route_agent


# --- Tools Node Creation ---

def resolve_all_tools(tools_dict=None) -> dict:
    """
    Resolves tools from MCP tools_dict and local feature modules (Cart, Negotiation, Recommedation, Order, Payment, Auth).
    Returns a unified dict mapping tool names to tool objects.
    """
    resolved_tools = {}
    if tools_dict:
        if isinstance(tools_dict, dict):
            resolved_tools.update(tools_dict)
        elif isinstance(tools_dict, list):
            for t in tools_dict:
                name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
                if name:
                    resolved_tools[name] = t

    # Ensure local feature tool suites are available
    for module_name, getter_name in [
        ("Cart.tools", "get_cart_langchain_tools"),
        ("Negotiation.tools", "get_negotiation_langchain_tools"),
        ("Recommedation.tools", "get_recommendation_langchain_tools"),
        ("Payment.tools", "get_payment_langchain_tools"),
        ("Order.tools", "get_order_langchain_tools"),
        ("Auth.tools", "get_auth_langchain_tools"),
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

    return resolved_tools


def create_tools_node(tools_dict=None):
    """
    Creates a dual sync/async tools execution node for the user agent graph.
    Resolves tools and executes tool calls concurrently in parallel via asyncio.gather.
    Propagates structured output and Generative UI cards back to AgentState.
    """
    resolved_tools = resolve_all_tools(tools_dict)

    def _sync_execute_tools(state: AgentState):
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {}

        def _exec_single(tool_call):
            tool_name = tool_call.get("name")
            tool_args = dict(tool_call.get("args") or {})
            call_id = tool_call.get("id")

            tool = resolved_tools.get(tool_name)
            if tool is None:
                return tool_name, call_id, tool_args, json.dumps({"error": f"Unknown tool '{tool_name}'"})

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
                res_text = _extract_text(raw_res)
            except Exception as e:
                res_text = json.dumps({"error": str(e)})

            return tool_name, call_id, tool_args, res_text

        import concurrent.futures
        if len(tool_calls) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tool_calls), 5)) as executor:
                results = list(executor.map(_exec_single, tool_calls))
        else:
            results = [_exec_single(tool_calls[0])]

        tool_messages = []
        updates = {}
        # Scoped strictly to current turn execution
        cards = []
        cart_modified = False
        cart_user_id = state.get("user_id", 0)

        for tool_name, call_id, tool_args, res_text in results:
            parsed = _safe_parse(res_text)
            if isinstance(parsed, dict):
                state_updates = _extract_state_updates_from_tool_result(tool_name, parsed)
                updates.update(state_updates)
                new_cards = _build_cards_from_tool(tool_name, parsed, state_updates, state)
                if new_cards:
                    cards.extend(new_cards)

                if tool_name in ("add_to_cart", "update_cart_quantity", "remove_from_cart") and parsed.get("success"):
                    cart_modified = True
                    cart_user_id = tool_args.get("user_id") or cart_user_id

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=call_id))

        if cart_modified and cart_user_id and cart_user_id > 0:
            try:
                from Cart.controller import cartController
                summary = asyncio.run(cartController.get_summary(user_id=cart_user_id))
                if summary and summary.get("success"):
                    updates["cart"] = summary.get("items", [])
                    updates["cart_items"] = summary.get("items", [])
                    updates["cart_total"] = summary.get("total_amount", 0.0)
                    updates["cart_subtotal"] = summary.get("subtotal", 0.0)
            except Exception:
                pass

        updates["cards"] = cards
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
        # Scoped strictly to current turn execution
        cards = []

        async def _execute_single_tool(tool_call):
            tool_name = tool_call.get("name")
            tool_args = dict(tool_call.get("args") or {})
            call_id = tool_call.get("id")

            tool = resolved_tools.get(tool_name)
            if tool is None:
                return tool_name, call_id, tool_args, json.dumps({"error": f"Unknown tool '{tool_name}'"})

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
                res_text = _extract_text(raw_res)
            except Exception as e:
                res_text = json.dumps({"error": str(e)})

            return tool_name, call_id, tool_args, res_text

        # Execute all tool calls concurrently in parallel
        results = await asyncio.gather(*[_execute_single_tool(tc) for tc in tool_calls])

        cart_modified = False
        cart_user_id = state.get("user_id", 0)

        for tool_name, call_id, tool_args, res_text in results:
            parsed = _safe_parse(res_text)
            if isinstance(parsed, dict):
                state_updates = _extract_state_updates_from_tool_result(tool_name, parsed)
                updates.update(state_updates)
                new_cards = _build_cards_from_tool(tool_name, parsed, state_updates, state)
                if new_cards:
                    cards.extend(new_cards)

                if tool_name in ("add_to_cart", "update_cart_quantity", "remove_from_cart") and parsed.get("success"):
                    cart_modified = True
                    cart_user_id = tool_args.get("user_id") or cart_user_id

            tool_messages.append(ToolMessage(content=res_text, tool_call_id=call_id))

        # Refresh cart summary once after all parallel tools complete
        if cart_modified and cart_user_id and cart_user_id > 0:
            try:
                from Cart.controller import cartController
                summary = await cartController.get_summary(user_id=cart_user_id)
                if summary and summary.get("success"):
                    updates["cart"] = summary.get("items", [])
                    updates["cart_items"] = summary.get("items", [])
                    updates["cart_total"] = summary.get("total_amount", 0.0)
                    updates["cart_subtotal"] = summary.get("subtotal", 0.0)
            except Exception:
                pass

        updates["cards"] = cards
        updates["messages"] = tool_messages
        return updates

    return RunnableLambda(_sync_execute_tools, afunc=_async_execute_tools)


# --- Graph Assembly ---

def initialize_agents(fast_llm, medium_llm=None, small_llm=None, tools_dict=None):
    """
    Initializes and returns the unified UserAgent and the tools node.
    Binds all tools directly to the single agent for zero-switch execution.
    """
    resolved_tools = resolve_all_tools(tools_dict)
    tools_list = list(resolved_tools.values())

    user_agent = UserAgent(fast_llm, tools=tools_list)
    tools_node = create_tools_node(resolved_tools)

    agents = {
        "agent": user_agent,
    }
    return agents, tools_node


def setup_nodes(workflow: StateGraph, agents: dict, tools_node):
    """Registers all workflow nodes to the StateGraph."""
    agent_node = RunnableLambda(agents["agent"].run, afunc=agents["agent"].arun)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("post_process", post_process_node)


def setup_edges(workflow: StateGraph):
    """
    Registers edges and routing logic for the unified user agent:
    1. 'agent' is the direct entry point.
    2. 'agent' routes to 'tools' if tool calls are present; otherwise routes to 'post_process'.
    3. 'tools' routes DIRECTLY back to 'agent' to synthesize results (no router/director ping-pong).
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

    # When tools finish, route directly back to the agent
    workflow.add_edge("tools", "agent")

    # Final step to completion
    workflow.add_edge("post_process", END)


def compile_agent_graph(fast_llm, medium_llm=None, small_llm=None, tools_dict=None):
    """Main orchestrator function that compiles the entire unified user agent graph."""
    workflow = StateGraph(AgentState)
    agents, tools_node = initialize_agents(fast_llm, medium_llm, small_llm, tools_dict)

    setup_nodes(workflow, agents, tools_node)
    setup_edges(workflow)

    checkpointer_instance = checkPointer.getCheckPointer(prefer="memory")
    return workflow.compile(checkpointer=checkpointer_instance)
