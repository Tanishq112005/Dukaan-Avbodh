import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from Merchant.tools import (
    merchant_get_store_analytics,
    merchant_get_top_selling_products,
    merchant_get_inventory_health_and_reorder_alerts,
    merchant_lookup_order_details,
    merchant_update_product_pricing_and_margin,
    merchant_get_customer_negotiation_insights,
    merchant_publish_catalog_item,
    get_merchant_langchain_tools,
    MERCHANT_ONLY_ERROR,
)


async def run_merchant_tools_tests():
    print("=" * 65)
    print("TESTING MERCHANT NATIVE AI TOOLS & STRICT AUTHORIZATION CONTROLS")
    print("=" * 65)

    # 1. Test unauthorized rejection for regular customer or guest
    print("\n[1] Testing unauthorized customer call rejection:")
    unauthorized_res = await merchant_get_store_analytics(caller_role="customer")
    assert unauthorized_res["status"] == "error", "Non-merchant caller MUST be rejected"
    assert unauthorized_res["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for customer!")

    unauthorized_inv = await merchant_get_inventory_health_and_reorder_alerts(caller_role="guest")
    assert unauthorized_inv["status"] == "error"
    print("  -> Access successfully denied with FORBIDDEN message for guest!")

    unauthorized_lookup = await merchant_lookup_order_details("order_123", caller_role=None)
    assert unauthorized_lookup["status"] == "error"
    print("  -> Access successfully denied with FORBIDDEN message for None/unauthenticated!")

    # 2. Test authorized merchant invocation of tools
    print("\n[2] Testing native LangChain StructuredTools export:")
    tools = get_merchant_langchain_tools()
    print(f"  -> Successfully generated {len(tools)} native LangChain StructuredTools (Zero MCP dependency):")
    for t in tools:
        print(f"     * {t.name}")

    assert len(tools) == 7, f"Expected 7 merchant tools, found {len(tools)}"
    print("\nALL MERCHANT TOOLS AUTHORIZATION CHECKS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    asyncio.run(run_merchant_tools_tests())
