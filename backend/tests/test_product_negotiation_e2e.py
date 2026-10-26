import asyncio
import sys
import os

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from config.database import db_connection
from sqlmodel import select
from Product.models import Product, ProductType, get_base_selling_price
from User.models import User, UserRole
from Cart.models import Cart, CartItem
from Cart.database import cart
from Cart.controller import cartController
from Cart.schemas import AddItemRequest, UpdateItemDiscountRequest
from Negotiation.controller import negotiationController
from Negotiation.schemas import ProductNegotiationRequest, NextDiscountRequest
from Negotiation.tools import negotiate_product_discount, negotiate_discount
from Cart.tools import add_to_cart, apply_cart_item_discount, get_cart_summary
from Order.database import orderRepository


async def run_e2e_verification():
    print("\n" + "=" * 60)
    print("STARTING E2E VERIFICATION: PER-PRODUCT NEGOTIATION (ALIGNED TO SELLING PRICE)")
    print("=" * 60)

    # 1. Setup Test User and Product in DB
    async with db_connection.get_session() as session:
        # Get or create user
        existing_user = (await session.exec(select(User))).first()
        if not existing_user:
            existing_user = User(
                name="E2E Test Shopper",
                email="shopper_e2e@dukaan.store",
                role=UserRole.CUSTOMER,
            )
            session.add(existing_user)
            await session.commit()
            await session.refresh(existing_user)

        test_user_id = existing_user.id

        # Clear existing test cart items for this user
        test_cart = (await session.exec(select(Cart).where(Cart.user_id == test_user_id))).first()
        if test_cart:
            items = (await session.exec(select(CartItem).where(CartItem.cart_id == test_cart.id))).all()
            for it in items:
                await session.delete(it)
            test_cart.discount_percentage = 0.0
            session.add(test_cart)
            await session.commit()

        # Find or create a test product
        prod = (await session.exec(select(Product).where(Product.stock > 10))).first()
        if not prod:
            prod = Product(
                name="E2E Test Designer Hoodie",
                price=1000.0,
                cost_price=600.0,
                min_profit_margin_percent=20.0,
                stock=50,
                type=ProductType.HOODIE,
                discount=15,  # 15% max merchant discount limit
            )
            session.add(prod)
            await session.commit()
            await session.refresh(prod)
        else:
            # Set known cost and margin for deterministic verification
            prod.price = 1000.0
            prod.cost_price = 600.0
            prod.min_profit_margin_percent = 20.0
            prod.discount = 15
            session.add(prod)
            await session.commit()
            await session.refresh(prod)

        prod_id = prod.id
        base_selling_price = get_base_selling_price(prod)
        print(f"[Setup] Using User ID {test_user_id} and Product ID {prod_id}: '{prod.name}' (Base Listing Selling Price: Rs.{base_selling_price}, DB price: Rs.{prod.price}, Cost: Rs.{prod.cost_price}, Margin: {prod.min_profit_margin_percent}%, Merchant Discount Ceiling: {prod.discount}%)")
        assert base_selling_price == 1176.0

    # =========================================================================
    # SCENARIO 1: Negotiate BEFORE adding item to cart
    # =========================================================================
    print("\n--- SCENARIO 1: Negotiate BEFORE adding item to cart ---")
    
    # Round 1: Customer asks for 20% discount (exceeds merchant ceiling of 15%)
    res1 = await negotiate_product_discount(
        product_id=prod_id,
        requested_discount_percent=20.0,
        user_id=test_user_id,
        current_discount_percent=0.0,
        quantity=1,
    )
    print(f"Round 1 Request: 20% | Response accepted: {res1['accepted']}, next_discount: {res1['next_discount_percent']}%, price: Rs.{res1['counter_offer_price']}, in_cart: {res1['in_cart']}")
    assert res1["success"] is True
    assert res1["accepted"] is False  # Cannot give full 20% because ceiling is 15%
    assert res1["next_discount_percent"] == 6.0
    assert res1["counter_offer_price"] == 1105.44  # 1176 * (1 - 0.06)
    assert res1["in_cart"] is False

    # Round 2: Customer counters asking for 10% discount (incremental step from 6.0% -> 9.6%)
    res2 = await negotiate_product_discount(
        product_id=prod_id,
        requested_discount_percent=10.0,
        user_id=test_user_id,
        current_discount_percent=6.0,
        quantity=1,
    )
    print(f"Round 2 Request: 10% from 6% | Response accepted: {res2['accepted']}, next_discount: {res2['next_discount_percent']}%, price: Rs.{res2['counter_offer_price']}")
    assert res2["success"] is True
    assert res2["accepted"] is False  # Incremental step gives 9.6%
    assert res2["next_discount_percent"] == 9.6
    assert res2["counter_offer_price"] == 1063.10  # 1176 * (1 - 0.096)

    # Round 3: Customer asks for 10% again from 9.6% -> now accepted!
    res3 = await negotiate_product_discount(
        product_id=prod_id,
        requested_discount_percent=10.0,
        user_id=test_user_id,
        current_discount_percent=9.6,
        quantity=1,
    )
    print(f"Round 3 Request: 10% from 9.6% | Response accepted: {res3['accepted']}, next_discount: {res3['next_discount_percent']}%, price: Rs.{res3['counter_offer_price']}")
    assert res3["success"] is True
    assert res3["accepted"] is True  # Fully accepted at 10.0%
    assert res3["next_discount_percent"] == 10.0
    assert res3["counter_offer_price"] == 1058.40  # 1176 * (1 - 0.10)

    # User accepts deal: Call add_to_cart with agreed discount_percentage
    add_res = await add_to_cart(
        product_id=prod_id,
        user_id=test_user_id,
        quantity=2,
        size="L",
        discount_percentage=res3["next_discount_percent"],
    )
    print(f"Added to Cart with agreed discount: {add_res}")
    assert add_res["success"] is True
    assert add_res["item"]["discount_percentage"] == 10.0
    assert add_res["item"]["discounted_price"] == 1058.40

    # Verify CartItem in DB directly
    summary1 = await get_cart_summary(user_id=test_user_id)
    print(f"Cart Summary after Scenario 1 add: Subtotal: Rs.{summary1['subtotal']}, Discount: Rs.{summary1['discount_amount']}, Total: Rs.{summary1['total_amount']}")
    assert summary1["subtotal"] == 2352.0  # 2 * 1176
    assert summary1["discount_amount"] == 235.20  # 10% of 2352
    assert summary1["total_amount"] == 2116.80  # 2 * 1058.40

    # =========================================================================
    # SCENARIO 2: Negotiate AFTER item is already in the cart
    # =========================================================================
    print("\n--- SCENARIO 2: Negotiate AFTER item is already in the cart ---")

    # Customer asks for further discount on the item already in the cart (asking for 14%)
    res4 = await negotiate_product_discount(
        product_id=prod_id,
        requested_discount_percent=14.0,  # Asking for 14% (up from 10%)
        user_id=test_user_id,
        current_discount_percent=0.0,    # Tool automatically detects current 10% from cart item in DB
        quantity=2,
        apply_to_cart=True,
    )
    print(f"In-Cart Negotiation Request: 14% | Accepted: {res4['accepted']}, next_discount: {res4['next_discount_percent']}%, price: Rs.{res4['counter_offer_price']}, updated_in_cart: {res4['updated_in_cart']}")
    assert res4["success"] is True
    assert res4["in_cart"] is True
    assert res4["updated_in_cart"] is True
    assert res4["current_discount_percent"] == 10.0  # Detected 10% from existing cart item
    assert res4["next_discount_percent"] == 12.0     # 10.0 + (15 - 10)*0.4 = 12.0%
    assert res4["counter_offer_price"] == 1034.88    # 1176 * (1 - 0.12)

    # Check updated cart summary
    summary2 = await get_cart_summary(user_id=test_user_id)
    expected_unit = res4["counter_offer_price"]
    expected_total = round(expected_unit * 2, 2)
    print(f"Cart Summary after Scenario 2: Subtotal: Rs.{summary2['subtotal']}, Discount: Rs.{summary2['discount_amount']}, Total: Rs.{summary2['total_amount']}")
    assert summary2["subtotal"] == 2352.0
    assert summary2["discount_amount"] == 282.24  # 12% of 2352
    assert round(summary2["total_amount"], 2) == expected_total  # 2069.76

    # =========================================================================
    # CONCURRENCY-LOCKED ORDER CHECKOUT
    # =========================================================================
    print("\n--- ORDER CHECKOUT WITH INDIVIDUAL ITEM DISCOUNT ---")
    orders = await orderRepository.create_order_with_lock(user_id=test_user_id)
    print(f"Created {len(orders)} order(s). Order 1 Total: Rs.{orders[0].total_amount}, Discount applied: {orders[0].discount_applied}%")
    assert len(orders) >= 1
    assert orders[0].discount_applied == res4["next_discount_percent"]
    assert round(orders[0].total_amount, 2) == expected_total

    # Cleanup test data
    async with db_connection.get_session() as session:
        for o in orders:
            await session.delete(o)
        t_cart = (await session.exec(select(Cart).where(Cart.user_id == test_user_id))).first()
        if t_cart:
            items = (await session.exec(select(CartItem).where(CartItem.cart_id == t_cart.id))).all()
            for it in items:
                await session.delete(it)
            t_cart.discount_percentage = 0.0
            session.add(t_cart)
        await session.commit()

    print("\n" + "=" * 60)
    print("ALL E2E VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_e2e_verification())
