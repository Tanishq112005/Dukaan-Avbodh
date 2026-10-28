import asyncio
import os
import sys
from datetime import datetime

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlmodel import select
from config.database import db_connection
from User.models import User
from Product.models import Product, get_base_selling_price
from Cart.models import Cart, CartItem
from Cart.database import cart
from Negotiation.controller import negotiationController
from Negotiation.schemas import NextDiscountRequest, ProductNegotiationRequest
from Order.database import orderRepository
from Chat.database import chat_audit_repo
from Merchant.database import merchantRepository
from agents.user.prompts import get_user_agent_prompt


async def run_tests():
    print("=" * 70)
    print("VERIFYING PER-PRODUCT DISCOUNT ISOLATION, COMBINED CART DISCOUNT,")
    print("AND MONGODB THREAD PERSISTENCE FOR MERCHANT DASHBOARD")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. SETUP
    # --------------------------------------------------------------------------
    async with db_connection.get_session() as session:
        user = (await session.exec(select(User))).first()
        assert user, "User not found in DB"
        user_id = user.id

        products = (await session.exec(select(Product).where(Product.stock > 10))).all()
        assert len(products) >= 2, "Need at least 2 products with stock > 10"
        p1, p2 = products[0], products[1]

    p1_price = get_base_selling_price(p1)
    p2_price = get_base_selling_price(p2)

    print(f"\n[1] SETUP:")
    print(f"  User ID: {user_id}")
    print(f"  Product 1: ID={p1.id}, Name='{p1.name}', Base Price=Rs.{p1_price}, Cost=Rs.{p1.cost_price}")
    print(f"  Product 2: ID={p2.id}, Name='{p2.name}', Base Price=Rs.{p2_price}, Cost=Rs.{p2.cost_price}")

    # --------------------------------------------------------------------------
    # 2. TEST 1: PER-PRODUCT DISCOUNT ISOLATION
    # --------------------------------------------------------------------------
    print("\n[2] TEST 1: Per-Product Discount Isolation (No Discount Bleed)")
    await cart.clear_cart(user_id=user_id)

    # User negotiates Product 1 and adds to cart with 10% discount
    disc_p1 = 10.0
    disc_price_p1 = round(p1_price * (1.0 - disc_p1 / 100.0), 2)
    await cart.add_item(
        user_id=user_id,
        product_id=p1.id,
        quantity=1,
        size="M",
        discount_percentage=disc_p1,
        discounted_price=disc_price_p1,
    )

    # User adds Product 2 WITHOUT negotiation -> MUST have 0.0% discount
    await cart.add_item(
        user_id=user_id,
        product_id=p2.id,
        quantity=1,
        size="L",
        discount_percentage=0.0,
        discounted_price=p2_price,
    )

    cart_items = await cart.get_items(user_id=user_id)
    assert len(cart_items) == 2, f"Expected 2 cart items, got {len(cart_items)}"

    item_map = {it["product_id"]: it for it in cart_items}
    item1 = item_map[p1.id]
    item2 = item_map[p2.id]

    print(f"  Cart Item 1 ({item1['name']}): Discount={item1['discount_percentage']}%, Price=Rs.{item1['price']}")
    print(f"  Cart Item 2 ({item2['name']}): Discount={item2['discount_percentage']}%, Price=Rs.{item2['price']}")

    assert item1["discount_percentage"] == disc_p1, f"Product 1 must have {disc_p1}% discount"
    assert item2["discount_percentage"] == 0.0, f"Product 2 must have 0% discount, but got {item2['discount_percentage']}%"
    print("  [PASS] Product 1 discount did NOT bleed into Product 2!")

    # Verify Prompt Isolation Instruction
    prompt_text = get_user_agent_prompt(
        user_id=user_id,
        negotiated_products={
            str(p1.id): {
                "product_id": p1.id,
                "product_name": p1.name,
                "discount_percentage": disc_p1,
                "discounted_price": disc_price_p1,
            }
        },
        cart_global_discount=0.0,
    )
    assert f"Product ID {p1.id}" in prompt_text
    assert "MANDATORY RULE: The above discounts apply ONLY to their specific product IDs" in prompt_text
    assert "pass discount_percentage=0.0" in prompt_text
    print("  [PASS] Agent prompt strictly enforces per-product discount isolation!")

    # --------------------------------------------------------------------------
    # 3. TEST 2: COMBINED CART DISCOUNT ON TOP OF INDIVIDUAL DISCOUNTS
    # --------------------------------------------------------------------------
    print("\n[3] TEST 2: Combined Cart Discount On Top of Item Discounts")
    totals_before = await cart.get_summary(user_id=user_id)
    print(f"  Before Cart Negotiation: Subtotal=Rs.{totals_before['subtotal']}, Total=Rs.{totals_before['total_amount']}")

    # User asks for a 5% discount across the cart
    cart_neg_res = await negotiationController.get_next_discount(
        NextDiscountRequest(
            user_id=user_id,
            requested_discount_percent=5.0,
            current_discount_percent=0.0,
            apply_to_cart=True,
        )
    )

    print(f"  Cart Negotiation Response: Accepted={cart_neg_res.accepted}, Next Discount={cart_neg_res.next_discount_percent}%, Counter Price=Rs.{cart_neg_res.counter_offer_price}")
    cart_global_disc = cart_neg_res.next_discount_percent
    assert cart_global_disc > 0, "Cart negotiation should offer a positive step discount"

    # Verify that individual item discounts were NOT overwritten in DB
    cart_items_after = await cart.get_items(user_id=user_id)
    item_map_after = {it["product_id"]: it for it in cart_items_after}
    assert item_map_after[p1.id]["discount_percentage"] == disc_p1, "Product 1 discount must still be 10%"
    assert item_map_after[p2.id]["discount_percentage"] == 0.0, "Product 2 discount must still be 0%"
    print("  [PASS] Individual CartItem discounts were preserved and NOT overwritten by cart discount!")

    # Verify Cart Totals
    totals_after = await cart.get_summary(user_id=user_id)
    expected_subtotal = round(p1_price + p2_price, 2)
    expected_items_disc = round(p1_price * (disc_p1 / 100.0), 2)
    expected_remaining = round(expected_subtotal - expected_items_disc, 2)
    expected_cart_disc = round(expected_remaining * (cart_global_disc / 100.0), 2)
    expected_total_disc = round(expected_items_disc + expected_cart_disc, 2)
    expected_final_total = round(expected_subtotal - expected_total_disc, 2)

    print(f"  Cart Totals After: Subtotal=Rs.{totals_after['subtotal']}, Discount Amount=Rs.{totals_after['discount_amount']}, Total=Rs.{totals_after['total_amount']}")
    print(f"  Expected Math: Subtotal=Rs.{expected_subtotal}, Total=Rs.{expected_final_total}")

    assert totals_after["subtotal"] == expected_subtotal
    assert abs(totals_after["total_amount"] - expected_final_total) <= 0.02, "Total amount matches combined discount math"
    print("  [PASS] Cart totals perfectly reflect combined sequential discount!")

    # --------------------------------------------------------------------------
    # 4. TEST 3: ORDER CHECKOUT WITH COMBINED DISCOUNT
    # --------------------------------------------------------------------------
    print("\n[4] TEST 3: Order Checkout with Combined Sequential Discount")
    orders = await orderRepository.create_order_with_lock(
        user_id=user_id,
        gateway_order_id="test_gw_order_combined_disc_001",
        provider="razorpay",
    )

    assert len(orders) == 2, f"Expected 2 order lines, got {len(orders)}"
    order_map = {o.product_id: o for o in orders}

    # Order 1 (Product 1): factor = (1 - 0.10) * (1 - cart_disc / 100)
    expected_o1_amount = round(p1_price * (1.0 - disc_p1 / 100.0) * (1.0 - cart_global_disc / 100.0), 2)
    # Order 2 (Product 2): factor = (1 - 0.00) * (1 - cart_disc / 100)
    expected_o2_amount = round(p2_price * (1.0 - 0.0 / 100.0) * (1.0 - cart_global_disc / 100.0), 2)

    o1 = order_map[p1.id]
    o2 = order_map[p2.id]

    print(f"  Order Row 1 ({p1.name}): Amount=Rs.{o1.total_amount}, Effective Discount Applied={o1.discount_applied}%")
    print(f"  Order Row 2 ({p2.name}): Amount=Rs.{o2.total_amount}, Effective Discount Applied={o2.discount_applied}%")

    assert abs(o1.total_amount - expected_o1_amount) <= 0.02, f"O1 amount mismatch: {o1.total_amount} vs {expected_o1_amount}"
    assert abs(o2.total_amount - expected_o2_amount) <= 0.02, f"O2 amount mismatch: {o2.total_amount} vs {expected_o2_amount}"

    total_orders_sum = round(o1.total_amount + o2.total_amount, 2)
    assert abs(total_orders_sum - totals_after["total_amount"]) <= 0.04, "Sum of orders matches cart total"
    print(f"  [PASS] Order checkout created rows with combined discounts, total Rs.{total_orders_sum} equals cart total!")

    # --------------------------------------------------------------------------
    # 5. TEST 4: MONGODB THREAD PERSISTENCE AND MERCHANT DASHBOARD
    # --------------------------------------------------------------------------
    print("\n[5] TEST 4: MongoDB Thread Persistence & Merchant Breakdown")
    test_thread_id = f"test_thread_neg_{int(datetime.utcnow().timestamp())}"

    # Simulate saving full thread turn with per-product negotiation state
    test_state_patch = {
        "negotiated_products": {
            str(p1.id): {
                "product_id": p1.id,
                "product_name": p1.name,
                "original_price": p1_price,
                "discount_percentage": disc_p1,
                "discounted_price": disc_price_p1,
            },
            str(p2.id): {
                "product_id": p2.id,
                "product_name": p2.name,
                "original_price": p2_price,
                "discount_percentage": 5.0,
                "discounted_price": round(p2_price * 0.95, 2),
            },
        },
        "cart_global_discount_percent": cart_global_disc,
        "negotiation_log": [
            {
                "product_id": p1.id,
                "product_name": p1.name,
                "original_price": p1_price,
                "requested": 15.0,
                "agent_offered": disc_p1,
                "counter_offer_price": disc_price_p1,
                "accepted": False,
                "scope": "product",
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "product_id": None,
                "product_name": "Full Shopping Cart",
                "original_price": expected_subtotal,
                "requested": 5.0,
                "agent_offered": cart_global_disc,
                "counter_offer_price": expected_final_total,
                "accepted": True,
                "scope": "cart",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
        "order_placed": True,
    }

    await chat_audit_repo.save_full_thread_turn(
        user_id=user_id,
        thread_id=test_thread_id,
        human_text="Can I get 15% discount on shirt and 5% on cart?",
        ai_text="I can offer 10% on shirt and extra discount on your cart!",
        state_patch=test_state_patch,
    )

    # Verify document in MongoDB
    saved_thread = await chat_audit_repo.get_thread(user_id=user_id, thread_id=test_thread_id)
    assert saved_thread is not None, "Thread document must exist in MongoDB"
    st = saved_thread.get("state") or {}
    assert "negotiated_products" in st, "state.negotiated_products must be stored in Mongo"
    assert str(p1.id) in st["negotiated_products"], f"Product {p1.id} must be in state.negotiated_products"
    assert st["cart_global_discount_percent"] == cart_global_disc, "cart_global_discount_percent must be saved"
    assert len(st["negotiation_log"]) == 2, "negotiation_log must be saved with 2 entries"
    print("  [PASS] MongoDB thread persisted per-product discounts and negotiation log successfully!")

    # Verify Merchant Analytics Funnel
    funnel = await merchantRepository._get_mongo_negotiation_funnel()
    print(f"  Merchant Funnel:")
    print(f"    Total Sessions: {funnel['total_chat_sessions']}")
    print(f"    Negotiation Rounds: {funnel['total_negotiation_rounds']}")
    print(f"    Agreed Deals: {funnel['agreed_deals_count']}")
    print(f"    Product Breakdown: {len(funnel.get('product_discount_breakdown', []))} items")

    breakdown = funnel.get("product_discount_breakdown", [])
    assert len(breakdown) > 0, "product_discount_breakdown should contain negotiated products"
    p1_breakdown = next((b for b in breakdown if str(b["product_id"]) == str(p1.id)), None)
    assert p1_breakdown is not None, f"Product {p1.id} should appear in merchant product breakdown"
    print(f"    Product {p1.id} ({p1_breakdown['product_name']}): Times Negotiated={p1_breakdown['negotiation_count']}, Avg Disc={p1_breakdown['average_discount_percent']}%, Max Disc={p1_breakdown['max_discount_percent']}%")
    print("  [PASS] Merchant can inspect per-product negotiation and discounts across all threads!")

    # Clean up test thread
    await chat_audit_repo.delete_thread(user_id=user_id, thread_id=test_thread_id)

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY! ZERO ERRORS OR REGRESSIONS DETECTED.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
