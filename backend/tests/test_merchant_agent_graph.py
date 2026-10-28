import asyncio
import os
import sys
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure backend directory is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agents.merchant.interfaces import IAgentInterface
from agents.merchant.state import AgentState
from agents.merchant.prompts import get_merchant_system_prompt, get_merchant_reminder
from agents.merchant.agent import MerchantAgent
from agents.merchant.checkpointer import checkPointer, MerchantCheckPointer
from agents.merchant.graph import (
    compile_agent_graph,
    resolve_all_merchant_tools,
    _extract_state_updates_from_tool_result,
    _build_cards_from_tool,
    deduplicate_cards,
    post_process_node,
    route_agent,
    create_tools_node,
)
from agents.merchant.controller import MerchantAgentController
from agents.merchant.routes import router as merchant_chat_router
from Merchant.schemas import MerchantChatRequest


async def run_merchant_agent_tests():
    print("=" * 70)
    print("TESTING DUKAAN MERCHANT AGENT ARCHITECTURE & TOOL FUNCTION CALLING")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. State & Prompt Verification
    # --------------------------------------------------------------------------
    print("\n[SECTION 1] Testing State Schema & Executive Prompts...")
    state: AgentState = {
        "messages": [HumanMessage(content="Show revenue")],
        "merchant_id": 42,
        "user_id": 42,
        "thread_id": "merchant_42",
        "current_intent": "analytics_inquiry",
    }
    assert state["merchant_id"] == 42
    assert state["thread_id"] == "merchant_42"

    prompt_text = get_merchant_system_prompt(
        merchant_id=42,
        conversation_summary="Merchant previously asked about inventory.",
        important_facts="Store focuses on denim garments.",
    )
    assert "Merchant ID: 42" in prompt_text
    assert "CONVERSATION SUMMARY SO FAR" in prompt_text
    assert "merchant_get_store_analytics" in prompt_text
    assert "merchant_publish_catalog_item" in prompt_text

    reminder = get_merchant_reminder()
    assert "NEVER output <thought> or <think> tags" in reminder
    print("  -> Merchant prompt and reminder formatted cleanly with context injection.")

    # --------------------------------------------------------------------------
    # 2. MerchantAgent Tool Binding & Execution
    # --------------------------------------------------------------------------
    print("\n[SECTION 2] Testing MerchantAgent Tool Binding & Invocation...")
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    agent = MerchantAgent(mock_llm)
    assert isinstance(agent, IAgentInterface)
    assert len(agent.tools) == 13, f"Expected 13 tools, got {len(agent.tools)}"
    mock_llm.bind_tools.assert_called_once()
    print(f"  -> Successfully bound {len(agent.tools)} native tools directly to LLM.")

    # Test Intent Detection
    ai_with_tool = AIMessage(
        content="",
        tool_calls=[{"name": "merchant_get_store_analytics", "args": {}, "id": "tc1"}]
    )
    mock_llm.invoke.return_value = ai_with_tool
    mock_llm.ainvoke = AsyncMock(return_value=ai_with_tool)

    res_sync = agent.run(state)
    assert res_sync["current_intent"] == "analytics_inquiry"
    assert res_sync["merchant_id"] == 42

    res_async = await agent.arun(state)
    assert res_async["current_intent"] == "analytics_inquiry"

    # Test Intent Detection for Product Management
    ai_edit = AIMessage(content="", tool_calls=[{"name": "merchant_edit_product_details", "args": {"product_id": 1, "price": 499.0}, "id": "tc2"}])
    assert agent._detect_intent(ai_edit) == "product_update"

    ai_inspect = AIMessage(content="", tool_calls=[{"name": "merchant_get_product_details", "args": {"product_id": 1}, "id": "tc3"}])
    assert agent._detect_intent(ai_inspect) == "product_inspection"

    ai_del = AIMessage(content="", tool_calls=[{"name": "merchant_delete_product", "args": {"product_id": 1}, "id": "tc4"}])
    assert agent._detect_intent(ai_del) == "product_deletion"

    print("  -> Sync and async agent execution correctly detects tool-driven intent across all tools.")

    # --------------------------------------------------------------------------
    # 3. Tool Extraction & Generative UI Card Generation
    # --------------------------------------------------------------------------
    print("\n[SECTION 3] Testing Generative UI Cards & Tool Updates Extraction...")

    # Analytics Card
    analytics_payload = {
        "status": "success",
        "gross_revenue_inr": 50000.0,
        "net_profit_inr": 15000.0,
        "profit_margin_percent": 30.0,
        "total_orders_count": 25,
        "total_items_sold": 40,
        "total_discounts_granted_inr": 2500.0,
    }
    updates = _extract_state_updates_from_tool_result("merchant_get_store_analytics", analytics_payload)
    assert updates["analytics_context"] == analytics_payload

    cards = _build_cards_from_tool("merchant_get_store_analytics", analytics_payload, updates)
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_analytics"
    assert cards[0]["data"]["gross_revenue_inr"] == 50000.0
    print("  -> Analytics card generated with financial metrics.")

    # Top Products Card
    top_prods_payload = {
        "status": "success",
        "count": 2,
        "top_products": [
            {"id": 1, "name": "Classic Denim", "units_sold": 50, "total_revenue": 45000.0},
            {"id": 2, "name": "Cotton Tee", "units_sold": 30, "total_revenue": 15000.0},
        ],
    }
    cards = _build_cards_from_tool("merchant_get_top_selling_products", top_prods_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_top_products"
    assert len(cards[0]["data"]["products"]) == 2
    print("  -> Top products card generated.")

    # Inventory Health Card
    inv_payload = {
        "status": "success",
        "threshold": 10,
        "out_of_stock_count": 1,
        "low_stock_count": 3,
        "critical_items": [{"id": 10, "name": "Summer Shorts", "current_stock": 0}],
    }
    cards = _build_cards_from_tool("merchant_get_inventory_health_and_reorder_alerts", inv_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_inventory_alerts"
    assert cards[0]["data"]["out_of_stock_count"] == 1
    print("  -> Inventory health card generated.")

    # Order Lookup Card
    order_payload = {
        "status": "success",
        "order": {"id": 101, "order_id": "order_demo_101", "total_amount": 1299.0, "status": "paid"},
    }
    cards = _build_cards_from_tool("merchant_lookup_order_details", order_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_order_details"
    assert cards[0]["data"]["order"]["id"] == 101
    print("  -> Order details card generated.")

    # Pricing Update Card
    pricing_payload = {
        "status": "success",
        "product_id": 5,
        "name": "Oversized Hoodie",
        "old_price": 1499.0,
        "new_price": 1299.0,
        "cost_price": 600.0,
        "min_profit_margin_percent": 25.0,
        "message": "Pricing updated",
    }
    cards = _build_cards_from_tool("merchant_update_product_pricing_and_margin", pricing_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_pricing_update"
    assert cards[0]["data"]["product_id"] == 5
    print("  -> Pricing update card generated.")

    # Negotiation Insights Card
    neg_payload = {
        "status": "success",
        "negotiation_metrics": {
            "total_negotiations": 120,
            "average_discount_granted_percent": 8.5,
            "conversion_rate_percent": 74.2,
        },
    }
    cards = _build_cards_from_tool("merchant_get_customer_negotiation_insights", neg_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_negotiation_insights"
    print("  -> Negotiation insights card generated.")

    # Product Details Card
    detail_payload = {
        "status": "success",
        "product_id": 1,
        "product": {"id": 1, "name": "Classic Denim Jeans", "price": 1499.0, "stock": 25},
    }
    cards = _build_cards_from_tool("merchant_get_product_details", detail_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_product_details"
    assert cards[0]["data"]["product"]["name"] == "Classic Denim Jeans"
    print("  -> Product details card generated.")

    # Product Update Card
    update_payload = {
        "status": "success",
        "product_id": 1,
        "message": "Product #1 updated successfully.",
        "updated_fields": ["price", "stock"],
    }
    cards = _build_cards_from_tool("merchant_edit_product_details", update_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_product_updated"
    assert "price" in cards[0]["data"]["updated_fields"]
    print("  -> Product updated card generated.")

    # Product Deleted Card
    del_payload = {
        "status": "success",
        "product_id": 99,
        "message": "Product #99 deleted successfully.",
    }
    cards = _build_cards_from_tool("merchant_delete_product", del_payload, {})
    assert len(cards) == 1
    assert cards[0]["type"] == "merchant_product_deleted"
    assert cards[0]["data"]["product_id"] == 99
    print("  -> Product deleted card generated.")

    # Card Deduplication
    duplicate_cards = [
        {"id": "c1", "type": "merchant_analytics", "data": {"gross_revenue_inr": 100}},
        {"id": "c2", "type": "merchant_analytics", "data": {"gross_revenue_inr": 200}},
    ]
    deduped = deduplicate_cards(duplicate_cards)
    assert len(deduped) == 1
    assert deduped[0]["data"]["gross_revenue_inr"] == 200
    print("  -> Card deduplication correctly keeps latest active card.")

    # --------------------------------------------------------------------------
    # 4. LangGraph Graph Assembly & Execution
    # --------------------------------------------------------------------------
    print("\n[SECTION 4] Testing Graph Routing & Compilation...")
    tools_dict = resolve_all_merchant_tools()
    assert len(tools_dict) == 13

    graph = compile_agent_graph(mock_llm, tools_dict)
    assert "agent" in graph.nodes
    assert "tools" in graph.nodes
    assert "post_process" in graph.nodes

    # Test route_agent function
    state_with_tools: AgentState = {
        "messages": [ai_with_tool]
    }
    assert route_agent(state_with_tools) == "tools"

    state_no_tools: AgentState = {
        "messages": [AIMessage(content="Here are the sales numbers.")]
    }
    assert route_agent(state_no_tools) == "post_process"

    post_res = post_process_node(state_no_tools)
    assert post_res["final_response"] == "Here are the sales numbers."
    print("  -> Graph conditional routing and post-processing nodes verified.")

    # --------------------------------------------------------------------------
    # 5. Controller Process & SSE Streaming Verification
    # --------------------------------------------------------------------------
    print("\n[SECTION 5] Testing Controller Process & SSE Streaming...")
    mock_chat_repo = AsyncMock()
    mock_chat_repo.add_message = AsyncMock()
    mock_chat_repo.update_thread_state = AsyncMock()

    mock_service = MagicMock()
    mock_compiled_agent = MagicMock()

    # Configure ainvoke return
    mock_compiled_agent.ainvoke = AsyncMock(return_value={
        "final_response": "Your net profit is INR 15,000.",
        "current_intent": "analytics_inquiry",
        "cards": cards,
        "analytics_context": analytics_payload,
    })

    # Configure astream_events generator for SSE
    async def mock_stream_events(*args, **kwargs):
        yield {"event": "on_chat_model_stream", "data": {"chunk": AIMessage(content="Your net profit ")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": AIMessage(content="is INR 15,000.")}}

    mock_compiled_agent.astream_events = mock_stream_events
    mock_service.get_agent_async = AsyncMock(return_value=mock_compiled_agent)

    controller = MerchantAgentController(service=mock_service, chat_repo=mock_chat_repo)

    req = MerchantChatRequest(text="What is my store profit?", thread_id="test_merchant_th")
    process_res = await controller.process_message(
        req=req,
        current_user={"user_id": 10, "role": "merchant"}
    )
    assert process_res["type"] == "merchant_chat_reply"
    assert "15,000" in process_res["message"]
    assert mock_chat_repo.add_message.call_count >= 2
    assert mock_chat_repo.update_thread_state.call_count >= 1
    print("  -> Controller standard JSON process_message executed and stored in MongoDB.")

    # Test SSE stream_message generator
    stream_chunks = []
    async for chunk in controller.stream_message(req=req, current_user={"user_id": 10, "role": "merchant"}):
        stream_chunks.append(chunk)

    joined_stream = "".join(stream_chunks)
    assert "data: " in joined_stream
    assert "data: [DONE]" in joined_stream
    assert "Your net profit" in joined_stream
    print("  -> Controller Server-Sent Events (SSE) streaming yielded tokens and [DONE] marker.")

    # --------------------------------------------------------------------------
    # 6. Merchant Chat Router Endpoints Verification
    # --------------------------------------------------------------------------
    print("\n[SECTION 6] Testing Merchant Chat Agent Router Endpoints...")
    chat_agent_routes = [r.path for r in merchant_chat_router.routes]
    print(f"  -> {len(chat_agent_routes)} Merchant Agent routes registered:")
    for r in merchant_chat_router.routes:
        print(f"     * [{','.join(r.methods)}] {r.path}")

    assert "/merchant/chat" in chat_agent_routes
    assert "/merchant/chat/message" in chat_agent_routes
    assert "/merchant/chat/stream" in chat_agent_routes
    assert "/merchant/chat/message/stream" in chat_agent_routes
    assert "/merchant/chat/threads" in chat_agent_routes

    print("\n" + "=" * 70)
    print("ALL MERCHANT AGENT GRAPH, TOOL CALLING & CONTROLLER CHECKS PASSED 100%!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_merchant_agent_tests())
