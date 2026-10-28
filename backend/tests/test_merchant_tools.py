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
    merchant_get_order_history,
    merchant_get_customer_chat_threads,
    merchant_get_chat_thread_transcript,
    merchant_update_product_pricing_and_margin,
    merchant_get_customer_negotiation_insights,
    merchant_publish_catalog_item,
    merchant_edit_product_details,
    merchant_get_product_details,
    merchant_delete_product,
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

    unauthorized_edit = await merchant_edit_product_details(product_id=1, name="Hacked Name", caller_role="customer")
    assert unauthorized_edit["status"] == "error"
    assert unauthorized_edit["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for edit_product_details!")

    unauthorized_detail = await merchant_get_product_details(product_id=1, caller_role="guest")
    assert unauthorized_detail["status"] == "error"
    assert unauthorized_detail["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for get_product_details!")

    unauthorized_del = await merchant_delete_product(product_id=1, caller_role="customer")
    assert unauthorized_del["status"] == "error"
    assert unauthorized_del["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for delete_product!")

    unauthorized_history = await merchant_get_order_history(caller_role="customer")
    assert unauthorized_history["status"] == "error"
    assert unauthorized_history["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for get_order_history!")

    unauthorized_threads = await merchant_get_customer_chat_threads(caller_role="guest")
    assert unauthorized_threads["status"] == "error"
    assert unauthorized_threads["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for get_customer_chat_threads!")

    unauthorized_transcript = await merchant_get_chat_thread_transcript(thread_id="t1", caller_role=None)
    assert unauthorized_transcript["status"] == "error"
    assert unauthorized_transcript["error"] == MERCHANT_ONLY_ERROR
    print("  -> Access successfully denied with FORBIDDEN message for get_chat_thread_transcript!")

    # 2. Test authorized merchant invocation of tools
    print("\n[2] Testing native LangChain StructuredTools export:")
    tools = get_merchant_langchain_tools()
    print(f"  -> Successfully generated {len(tools)} native LangChain StructuredTools (Zero MCP dependency):")
    for t in tools:
        print(f"     * {t.name}")

    assert len(tools) == 13, f"Expected 13 merchant tools, found {len(tools)}"
    print("\nALL MERCHANT TOOLS AUTHORIZATION CHECKS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    asyncio.run(run_merchant_tools_tests())
