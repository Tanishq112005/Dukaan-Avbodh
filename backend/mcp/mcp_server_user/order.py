from typing import List, Optional
from mcp_server_user.server import mcp
from repositories import OrderRepository, UserRepository, ProductRepository, DiscountPolicyRepository
from repositories.campain_repository import CampaignRepository
from models import Order
from config.database import db_connection
from sqlmodel import select
from models.user import User
from services.payment_service import rzp_client, check_user_payment_status
from utils.pricing_math import AGENT_MAX_DISCOUNT_PERCENT
import os
from dotenv import load_dotenv
order_repo = OrderRepository()
user_repo = UserRepository()
product_repo = ProductRepository()
discount_repo = DiscountPolicyRepository()
campaign_repo = CampaignRepository()


load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@mcp.tool()
async def create_order(
    user_id: int, 
    product_ids: List[int], 
    name: str, 
    email: str, 
    address: str, 
    discount: float = 0.0,
    thread_id: str = ""
) -> dict:
    """
    Creates a new order for multiple products, applies bounded discounts, and generates a Razorpay payment link.
    
    LLM Instructions:
    - FIRST call get_user_details. Confirm saved address or collect only missing fields.
    - Pass the confirmed name, email, address, user_id, product_ids, and negotiated discount.
    - When you receive the response, ALWAYS share the 'payment_link' as a markdown link [Pay now](url)
      AND as a raw URL on its own line so the customer can click it.
    """
    await user_repo.ensure_guest_exists(user_id)
    
    async with db_connection.get_session() as session:
        user = (await session.exec(select(User).where(User.id == user_id))).first()
        if user:
            user.name = name
            user.identifier = email
            user.address = address
            session.add(user)
            await session.commit()
    
    from services.combo_pricing_engine import combo_pricing_engine
    from services.pricing_service import pricing_service
    
    from repositories.cart_repository import cart_repository
    cart_items = await cart_repository.get_cart_items(user_id)
    if not cart_items:
        return {"success": False, "reason": "Cart is empty."}
        
    db_products = []
    for item in cart_items:
        product = await product_repo.get_by_id(item["id"])
        if not product or product.stock <= 0:
            return {"success": False, "reason": f"Product {item['name']} is out of stock or does not exist."}
        # handle multiple quantities if needed, though mostly 1 in dukaan
        for _ in range(item.get("quantity", 1)):
            db_products.append(product)
        
    priced_items = await pricing_service.price_cart_items([
        {"id": p.id, "quantity": 1, "product": p, "type": p.type, "price": p.price}
        for p in db_products
    ])
    
    # 2. Get the actual negotiated discount from the thread state (or fallback to LLM's discount)
    final_discount = discount
    if thread_id:
        from repositories.chat_audit_repository import chat_audit_repo
        thread = await chat_audit_repo.collection.find_one({"user_id": user_id, "thread_id": thread_id})
        if thread and "state" in thread:
            # We trust the state's discount more than the LLM's hallucinated args
            state_discount = thread["state"].get("current_discount_percent", 0.0)
            if state_discount > 0:
                final_discount = state_discount

    # 3. Calculate exact combo price including sequential campaigns + extra discount
    combo = combo_pricing_engine.calculate_combo_price(priced_items, final_discount)
    
    final_total_price = combo.get("final_price", 0.0)
    total_price = combo.get("subtotal", 0.0)
    # This represents the TOTAL discount percentage (campaigns + extra) off the original list price
    # which is what Analytics Service and Order DB need.
    total_effective_discount_percent = combo.get("effective_discount_percent", 0.0)
    
    final_amount_paise = int(final_total_price * 100)

    payment_link_url = None
    payment_link_id = None
    razorpay_order_id = None
    
    if rzp_client and final_amount_paise >= 100:
        try:
            rzp_order = rzp_client.order.create({
                "amount": final_amount_paise,
                "currency": "INR",
                "receipt": f"receipt_user_{user_id}",
                "notes": {
                    "ai_discount_applied": str(final_discount),
                    "original_price": str(total_price)
                }
            })
            razorpay_order_id = rzp_order.get("id")
            
            pl_response = rzp_client.payment_link.create({
                "amount": final_amount_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": "Dukkan AI Shopping Agent Order",
                "customer": {
                    "name": name,
                    "email": email,
                },
                "notify": {
                    "email": True
                },
                "reminder_enable": True,
                "callback_url": f"{FRONTEND_URL.rstrip('/')}/order-confirmed",
                "callback_method": "get",
                "notes": {
                    "order_id": razorpay_order_id,
                    "user_id": str(user_id),
                }
            })
            payment_link_url = pl_response.get("short_url")
            payment_link_id = pl_response.get("id")
            
        except Exception as e:
            print(f"[RAZORPAY ERROR] Failed to create payment link: {e}")
            return {
                "success": False,
                "error": "I am so sorry, but our payment gateway (Razorpay) is temporarily down. Your cart is saved securely. Can we try again in a few minutes?"
            }

    created_order_ids = []
    for product in db_products:
        order = Order(
            product_id=product.id,
            user_id=user_id,
            discount_applied=total_effective_discount_percent,
            status="pending_payment",
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_link_id=payment_link_id,
            payment_link_url=payment_link_url,
        )
        created = await order_repo.create(order)
        created_order_ids.append(created.id)
        
        await product_repo.update_stock(product.id, product.stock - 1)
        # Keeps each linked campaign's total_items_sold counter (sales performance) in sync.
        await campaign_repo.record_product_sale(product.id, 1)
        
    from services.audit_logger import audit_logger
    ordered_meta = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image_url": product.image_url,
        }
        for product in db_products
    ]
    order_group_id = razorpay_order_id or payment_link_id or f"order_{user_id}_{created_order_ids[0] if created_order_ids else 'na'}"
    await audit_logger.log_action(
        action="create_order",
        reason=(
            f"Placed one checkout for {len(db_products)} item(s). "
            f"extra_discount={final_discount}%, effective={total_effective_discount_percent}%"
        ),
        result=(
            f"order_ids={created_order_ids} total={final_total_price} "
            f"list={round(total_price, 2)} status=pending_payment"
        ),
        user_id=user_id,
        thread_id=str(thread_id) if thread_id else None,
        metadata={
            "kind": "order",
            "is_order": True,
            "order_group_id": order_group_id,
            "order_ids": created_order_ids,
            "products": ordered_meta,
            "discount_applied": total_effective_discount_percent,
            "extra_discount_percent": final_discount,
            "final_total_price": final_total_price,
            "subtotal": round(total_price, 2),
        },
    )
        
    try:
        if thread_id:
            from repositories.chat_audit_repository import chat_audit_repo
            await chat_audit_repo.update_state_patch(user_id, thread_id, {
                "order_placed": True,
                "razorpay_id": razorpay_order_id,
                "payment_status": "pending_payment",
                "user_info": {"name": name, "email": email},
                "ordered_products": ordered_meta,
                "cart_products": ordered_meta,
                "combo_offer": None,
            })
    except Exception as e:
        print(f"Failed to update chat audit for order: {e}")

    return {
        "success": True,
        "order_ids": created_order_ids,
        "razorpay_order_id": razorpay_order_id,
        "payment_link_id": payment_link_id,
        "payment_link": payment_link_url or "Payment Link Unavailable (API Error)",
        "requested_discount": discount,
        "discount_applied": total_effective_discount_percent,
        "total_price_before_discount": round(total_price, 2),
        "final_total_price": final_total_price
    }


@mcp.tool()
async def check_payment_status(user_id: int, thread_id: str = "") -> dict:
    """
    Checks whether the shopper finished paying on the Razorpay payment link.

    LLM Instructions:
    - Call this when the user says they paid, or on [SYSTEM EVENT: payment].
    - If paid is true, congratulate them and then clear_cart.
    - If paid is false, tell them payment is not confirmed yet and reshare payment_link.
    """
    res = await check_user_payment_status(user_id)
    
    if thread_id and res.get("paid"):
        try:
            from repositories.chat_audit_repository import chat_audit_repo
            await chat_audit_repo.update_state_patch(user_id, thread_id, {
                "payment_status": "paid"
            })
        except Exception as e:
            pass
            
    return res
