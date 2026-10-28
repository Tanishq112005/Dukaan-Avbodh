import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from Merchant.models import (
    MerchantDiscountPolicy,
    DiscountPolicy,
)
from Merchant.schemas import (
    MerchantDashboardAnalyticsResponse,
    PricingBoundsUpdateRequest,
    UpdateOrderStatusRequest,
    MerchantChatRequest,
)
from Merchant.utils import (
    resolve_time_range,
    calculate_profit_margin,
    calculate_discount_amount,
    get_stock_status,
    format_inr_currency,
    verify_merchant_role,
    assert_merchant_access,
)
from Merchant.tools import (
    merchant_get_store_analytics,
    merchant_get_top_selling_products,
    merchant_get_inventory_health_and_reorder_alerts,
    merchant_lookup_order_details,
    merchant_update_product_pricing_and_margin,
    merchant_get_customer_negotiation_insights,
    merchant_publish_catalog_item,
    merchant_edit_product_details,
    merchant_get_product_details,
    merchant_delete_product,
    get_merchant_langchain_tools,
    MERCHANT_ONLY_ERROR,
)
from Merchant.database import merchantChatRepo
from Merchant.controller import merchantController
from Merchant.routes import router as merchant_router
from fastapi import HTTPException


async def run_merchant_e2e_tests():
    print("=" * 70)
    print("STARTING DUKAAN UNIFIED MERCHANT DOMAIN COMPREHENSIVE E2E TEST SUITE")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. Models and Schemas Validation (Clean, Non-Campaign)
    # --------------------------------------------------------------------------
    print("\n[SECTION 1] Validating Models & Schemas...")
    policy = MerchantDiscountPolicy(
        max_discount_percentage=30.0,
        min_margin_percentage=20.0,
    )
    assert policy.max_discount_percentage == 30.0
    print("  -> MerchantDiscountPolicy model validated")

    disc_policy = DiscountPolicy(
        product_id=1,
        max_discount_percent=25.0,
    )
    assert disc_policy.max_discount_percent == 25.0
    print("  -> DiscountPolicy model validated")

    req = PricingBoundsUpdateRequest(
        max_discount_percentage=22.0,
        min_margin_percentage=18.0,
    )
    assert req.max_discount_percentage == 22.0
    print("  -> PricingBoundsUpdateRequest schema validated")

    # --------------------------------------------------------------------------
    # 2. Utility Helper Functions
    # --------------------------------------------------------------------------
    print("\n[SECTION 2] Validating Utility Helper Functions...")
    assert resolve_time_range("all") is None
    assert resolve_time_range("today") is not None
    assert resolve_time_range("7d") is not None
    assert resolve_time_range("30d") is not None
    print("  -> resolve_time_range for today, 7d, 30d, all passed")

    margin = calculate_profit_margin(revenue=1000.0, cost=650.0)
    assert margin == 35.0, f"Expected 35.0, got {margin}"
    print(f"  -> calculate_profit_margin (1000 rev, 650 cost) = {margin}%")

    disc = calculate_discount_amount(original_price=1200.0, discount_percent=10.0)
    assert disc == 120.0, f"Expected 120.0, got {disc}"
    print(f"  -> calculate_discount_amount (1200 price, 10% disc) = INR {disc}")

    assert get_stock_status(0) == "Out of Stock"
    assert get_stock_status(-2) == "Out of Stock"
    assert get_stock_status(4) == "Low Stock"
    assert get_stock_status(10) == "Low Stock"
    assert get_stock_status(15) == "In Stock"
    print("  -> get_stock_status classification rules passed")

    formatted = format_inr_currency(123456.78)
    assert "123,456.78" in formatted
    print("  -> format_inr_currency passed")

    assert verify_merchant_role({"role": "merchant"}) is True
    assert verify_merchant_role({"role": "customer"}) is False
    assert verify_merchant_role(None) is False

    try:
        assert_merchant_access({"role": "customer"})
        assert False, "Should raise 403 HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
        print("  -> assert_merchant_access strictly rejected non-merchant with HTTP 403")

    # --------------------------------------------------------------------------
    # 3. Strict Merchant-Only Tool Authorization (All 7 Native Tools)
    # --------------------------------------------------------------------------
    print("\n[SECTION 3] Validating Merchant AI Tools Authorization (Strictly Merchant-Only)...")
    roles_to_block = ["customer", "guest", "anonymous", "", None]
    for bad_role in roles_to_block:
        res = await merchant_get_store_analytics(caller_role=bad_role)
        assert res["status"] == "error", f"Role '{bad_role}' MUST be blocked from store analytics"
        assert res["error"] == MERCHANT_ONLY_ERROR

        res2 = await merchant_get_top_selling_products(caller_role=bad_role)
        assert res2["status"] == "error"
        assert res2["error"] == MERCHANT_ONLY_ERROR

        res3 = await merchant_get_inventory_health_and_reorder_alerts(caller_role=bad_role)
        assert res3["status"] == "error"
        assert res3["error"] == MERCHANT_ONLY_ERROR

        res4 = await merchant_lookup_order_details("order_123", caller_role=bad_role)
        assert res4["status"] == "error"
        assert res4["error"] == MERCHANT_ONLY_ERROR

        res5 = await merchant_update_product_pricing_and_margin(product_id=1, new_price=999, caller_role=bad_role)
        assert res5["status"] == "error"
        assert res5["error"] == MERCHANT_ONLY_ERROR

        res6 = await merchant_get_customer_negotiation_insights(caller_role=bad_role)
        assert res6["status"] == "error"
        assert res6["error"] == MERCHANT_ONLY_ERROR

        res7 = await merchant_publish_catalog_item(
            name="Test Tee", price=599, stock=10, product_type="t-shirt", caller_role=bad_role
        )
        assert res7["status"] == "error"
        assert res7["error"] == MERCHANT_ONLY_ERROR

        res8 = await merchant_edit_product_details(product_id=1, name="Hacked", caller_role=bad_role)
        assert res8["status"] == "error"
        assert res8["error"] == MERCHANT_ONLY_ERROR

        res9 = await merchant_get_product_details(product_id=1, caller_role=bad_role)
        assert res9["status"] == "error"
        assert res9["error"] == MERCHANT_ONLY_ERROR

        res10 = await merchant_delete_product(product_id=1, caller_role=bad_role)
        assert res10["status"] == "error"
        assert res10["error"] == MERCHANT_ONLY_ERROR

    print("  -> 100% of all 10 tools strictly blocked non-merchant callers with FORBIDDEN status!")

    langchain_tools = get_merchant_langchain_tools()
    assert len(langchain_tools) == 10
    print(f"  -> All {len(langchain_tools)} native LangChain structured tools verified.")

    # --------------------------------------------------------------------------
    # 4. Controller, Repository Analytics & Dedicated MongoDB Chat Storage
    # --------------------------------------------------------------------------
    print("\n[SECTION 4] Validating Controller & Repository Analytics...")
    from config.database import db_connection
    await db_connection.init_db()

    analytics_data = await merchantController.get_dashboard_analytics("all")
    assert "metrics" in analytics_data
    assert "top_selling_products" in analytics_data
    assert "inventory_alerts" in analytics_data
    assert "revenue_by_category" in analytics_data
    assert "revenue_trend" in analytics_data
    assert "negotiation_analytics" in analytics_data

    metrics = analytics_data["metrics"]
    print(f"  -> Analytics computed: Total Revenue = INR {metrics.get('total_revenue')}, Net Profit = INR {metrics.get('total_profit')}, Margin = {metrics.get('profit_margin_percent')}%")
    print(f"  -> Top Selling Products: {len(analytics_data['top_selling_products'])} products ranked")
    print(f"  -> Categories: {[c['name'] for c in analytics_data['revenue_by_category']]}")

    orders = await merchantController.get_all_orders(limit=10)
    print(f"  -> Orders retrieved: {len(orders)} order groups loaded")

    alerts = await merchantController.get_inventory_alerts(threshold=15)
    print(f"  -> Inventory alerts: {len(alerts)} items flagged for low/out-of-stock")

    bounds = await merchantController.get_pricing_bounds()
    assert "max_discount_percentage" in bounds
    print(f"  -> Pricing negotiation bounds: Max Discount = {bounds['max_discount_percentage']}%, Min Margin = {bounds['min_margin_percentage']}%")

    # Test Dedicated MongoDB Merchant Chats Table
    print("\n[SECTION 4b] Testing Dedicated MongoDB 'merchant_chats' Collection...")
    test_merchant_id = 9999
    test_thread = f"merchant_test_{test_merchant_id}"

    # 1. Add merchant message
    await merchantChatRepo.add_message(
        merchant_id=test_merchant_id,
        thread_id=test_thread,
        role="merchant",
        content="What is my total store profit?",
    )

    # 2. Add assistant message & update state snapshot
    test_state_snapshot = {
        "current_intent": "analytics_inquiry",
        "last_tool_called": "merchant_get_store_analytics",
        "analytics_context": {"total_profit": 14433.92},
    }
    await merchantChatRepo.add_message(
        merchant_id=test_merchant_id,
        thread_id=test_thread,
        role="assistant",
        content="Your net store profit is INR 14,433.92 with a 30.5% margin.",
    )
    await merchantChatRepo.update_thread_state(
        merchant_id=test_merchant_id,
        thread_id=test_thread,
        state_snapshot=test_state_snapshot,
    )

    # 3. Retrieve thread from merchant_chats table
    fetched_threads = await merchantController.get_merchant_chat_threads(merchant_id=test_merchant_id, limit=5)
    assert len(fetched_threads) >= 1, "Expected thread stored in MongoDB 'merchant_chats'"
    saved_th = fetched_threads[0]
    assert saved_th["thread_id"] == test_thread
    assert len(saved_th.get("messages", [])) >= 2
    assert saved_th.get("state", {}).get("current_intent") == "analytics_inquiry"
    print(f"  -> Successfully verified dedicated MongoDB 'merchant_chats' storage with {len(saved_th['messages'])} messages and audited state snapshot!")

    # --------------------------------------------------------------------------
    # 5. Route Endpoints Verification
    # --------------------------------------------------------------------------
    print("\n[SECTION 5] Validating FastAPI Router Endpoints...")
    registered_routes = [route.path for route in merchant_router.routes]
    print(f"  -> {len(registered_routes)} Merchant routes registered:")
    for r in merchant_router.routes:
        methods = ",".join(r.methods)
        print(f"     * [{methods}] {r.path}")

    assert "/merchant/analytics" in registered_routes
    assert "/merchant/orders" in registered_routes
    assert "/merchant/orders/{order_id}" in registered_routes
    assert "/merchant/inventory-alerts" in registered_routes
    assert "/merchant/audit-logs" in registered_routes
    assert "/merchant/chat-threads" in registered_routes
    assert "/merchant/merchant-chats" in registered_routes
    assert "/merchant/pricing-bounds" in registered_routes
    assert "/merchant/chat" in registered_routes

    print("\n" + "=" * 70)
    print("ALL DUKAAN UNIFIED MERCHANT DOMAIN E2E TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_merchant_e2e_tests())
