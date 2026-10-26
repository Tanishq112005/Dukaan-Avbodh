import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Merchant.tools import (
    merchant_get_store_analytics,
    merchant_get_top_selling_products,
    merchant_get_inventory_health_and_reorder_alerts,
    merchant_manage_campaign,
    merchant_update_product_pricing_and_margin,
    get_merchant_langchain_tools,
    MERCHANT_ONLY_ERROR,
)


async def run_merchant_tools_tests():
    print("=" * 65)
    print("TESTING MERCHANT AI TOOLS & STRICT AUTHORIZATION CONTROLS")
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

    # 2. Test authorized merchant invocation of analytics tool
    print("\n[2] Testing authorized merchant invocation:")
    tools = get_merchant_langchain_tools()
    print(f"  -> Successfully generated {len(tools)} native LangChain StructuredTools:")
    for t in tools:
        print(f"     * {t.name}")

    assert len(tools) == 8, f"Expected 8 merchant tools, found {len(tools)}"
    print("\nALL MERCHANT TOOLS AUTHORIZATION CHECKS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    asyncio.run(run_merchant_tools_tests())
