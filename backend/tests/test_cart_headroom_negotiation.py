import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlmodel import select
from config.database import db_connection
from User.models import User
from Product.models import Product, ProductType
from Cart.models import Cart, CartItem
from Cart.database import cart
from Negotiation.controller import negotiationController
from Negotiation.schemas import NextDiscountRequest
from Negotiation.utils import calculate_cart_discount_headroom


async def run_test():
    print("=" * 60)
    print("VERIFYING CART-LEVEL NEGOTIATION WITH HEADROOM & STEP-WISE OFFERS")
    print("=" * 60)

    # 1. Setup existing user and two test products
    async with db_connection.get_session() as session:
        user = (await session.exec(select(User))).first()
        assert user, "User not found in DB"
        user_id = user.id

        products = (await session.exec(select(Product).where(Product.stock > 5))).all()
        assert len(products) >= 2, "Need at least 2 products with stock > 5"
        p1, p2 = products[0], products[1]

    print(f"[Setup] User ID: {user_id}")
    print(f"  Product 1: '{p1.name}' (Price: Rs.{p1.price}, Cost: Rs.{p1.cost_price}, Margin: {p1.min_profit_margin_percent}%, Merchant Disc: {p1.discount}%)")
    print(f"  Product 2: '{p2.name}' (Price: Rs.{p2.price}, Cost: Rs.{p2.cost_price}, Margin: {p2.min_profit_margin_percent}%, Merchant Disc: {p2.discount}%)")

    # 2. Clear cart and add Item 1 with 2% initial discount, and Item 2 with 0% discount
    from Product.models import get_base_selling_price
    orig_p1 = get_base_selling_price(p1)
    orig_p2 = get_base_selling_price(p2)

    await cart.clear_cart(user_id=user_id)
    await cart.add_item(
        user_id=user_id,
        product_id=p1.id,
        quantity=1,
        size="M",
        discount_percentage=2.0,
        discounted_price=round(orig_p1 * 0.98, 2),
    )
    await cart.add_item(
        user_id=user_id,
        product_id=p2.id,
        quantity=1,
        size="L",
        discount_percentage=0.0,
        discounted_price=orig_p2,
    )

    summary_before = await cart.get_summary(user_id=user_id)
    print(f"[Initial Cart] Subtotal: Rs.{summary_before['subtotal']}, Discount: Rs.{summary_before.get('discount_amount', 0.0)}, Total: Rs.{summary_before.get('total_amount', 0.0)}")

    # 3. Check headroom calculation
    detailed_items = await negotiationController.db.get_cart_items_detailed(user_id=user_id)
    headroom = calculate_cart_discount_headroom(detailed_items)
    print(f"[Headroom Check]")
    print(f"  Total Original: Rs.{headroom['total_original_price']}")
    print(f"  Current Selling Total: Rs.{headroom['current_cart_total']}")
    print(f"  Total Wholesale Cost: Rs.{headroom['total_cost_price']}")
    print(f"  Total Minimum Safe Floor: Rs.{headroom['total_minimum_selling_price']}")
    print(f"  Current Effective Discount %: {headroom['current_effective_discount_pct']}%")
    print(f"  Absolute Max Ceiling (Upper Limit): {headroom['absolute_max_ceiling']}%")

    assert headroom['current_effective_discount_pct'] > 0, "Initial effective discount should reflect Item 1's 10% discount"
    ceiling = headroom['absolute_max_ceiling']
    assert ceiling <= 15.0, "Ceiling must not exceed AGENT_MAX_DISCOUNT_PERCENT"

    # 4. Round 1 of Cart Negotiation: User asks for 15% discount on the cart
    print("\n--- ROUND 1: Customer asks for 15% off the cart ---")
    r1 = await negotiationController.get_next_discount(NextDiscountRequest(
        user_id=user_id,
        requested_discount_percent=15.0,
        current_discount_percent=0.0,
        apply_to_cart=True,
    ))
    print(f"  Response: Accepted={r1.accepted}, Next Discount={r1.next_discount_percent}%, Counter Price=Rs.{r1.counter_offer_price}, Ceiling={r1.absolute_max_discount_percent}%")
    print(f"  Reason: {r1.reason}")
    assert r1.next_discount_percent > headroom['current_effective_discount_pct'], "Round 1 should concede a step above initial discount"
    assert r1.next_discount_percent <= ceiling, "Offer must not exceed upper limit ceiling"

    # 5. Round 2: Customer pushes for even more discount
    print(f"\n--- ROUND 2: Customer counters, asking for more (15%) ---")
    r2 = await negotiationController.get_next_discount(NextDiscountRequest(
        user_id=user_id,
        requested_discount_percent=15.0,
        current_discount_percent=r1.next_discount_percent,
        apply_to_cart=True,
    ))
    print(f"  Response: Accepted={r2.accepted}, Next Discount={r2.next_discount_percent}%, Counter Price=Rs.{r2.counter_offer_price}")
    print(f"  Reason: {r2.reason}")
    assert r2.next_discount_percent >= r1.next_discount_percent, "Round 2 concession must be >= Round 1"
    assert r2.next_discount_percent <= ceiling, "Offer must not exceed ceiling"

    # 6. Round 3: Customer asks for excessive 40% discount (must be capped at upper limit)
    print("\n--- ROUND 3: Customer asks for unreasonable 40% discount ---")
    r3 = await negotiationController.get_next_discount(NextDiscountRequest(
        user_id=user_id,
        requested_discount_percent=40.0,
        current_discount_percent=r2.next_discount_percent,
        apply_to_cart=True,
    ))
    print(f"  Response: Accepted={r3.accepted}, Next Discount={r3.next_discount_percent}%, Ceiling={r3.absolute_max_discount_percent}%")
    assert r3.accepted is False, "40% discount must NOT be accepted"
    assert r3.next_discount_percent <= ceiling, "Discount must never breach upper limit ceiling"

    # 7. Verify Cart Item States in Database
    summary_after = await cart.get_summary(user_id=user_id)
    items_after = await cart.get_items(user_id=user_id)
    print(f"\n[Final Cart Summary in DB] Subtotal: Rs.{summary_after['subtotal']}, Discount: Rs.{summary_after.get('discount_amount', 0.0)}, Total: Rs.{summary_after.get('total_amount', 0.0)}")
    for it in items_after:
        print(f"  Item {it['product_id']}: '{it['name']}' -> Original: Rs.{it['original_price']}, Discount: {it['discount_percentage']}%, Price: Rs.{it['price']}")
        assert it['discount_percentage'] >= 2.0 or it['product_id'] == p2.id, "Existing higher discounts must be preserved"
        cost = p1.cost_price if it['product_id'] == p1.id else p2.cost_price
        assert it['price'] >= cost, "Selling price must not breach wholesale cost"

    print("\n" + "=" * 60)
    print("ALL CART-LEVEL NEGOTIATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_test())
