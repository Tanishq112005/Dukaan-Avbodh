from typing import List, Optional
from mcp_server_user.server import mcp
from repositories import OrderRepository, UserRepository, ProductRepository, DiscountPolicyRepository
from models import Order
from config.database import db_connection
from sqlmodel import select
from models.user import User
from services.payment_service import rzp_client, check_user_payment_status
from utils.pricing_math import AGENT_MAX_DISCOUNT_PERCENT
import os

order_repo = OrderRepository()
user_repo = UserRepository()
product_repo = ProductRepository()
discount_repo = DiscountPolicyRepository()

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
    
    products = []
    total_price = 0.0
    max_discount_allowed_amount = 0.0
    
    for pid in product_ids:
        product = await product_repo.get_by_id(pid)
        if not product or product.stock <= 0:
            return {"success": False, "reason": f"Product ID {pid} is out of stock or does not exist."}
        
        products.append(product)
        total_price += product.price
        
        policy = await discount_repo.get_for_product(pid)
        if policy:
            max_discount_allowed_amount += (product.price * min(policy.max_discount_percent, AGENT_MAX_DISCOUNT_PERCENT) / 100)
        else:
            max_discount_allowed_amount += (product.price * AGENT_MAX_DISCOUNT_PERCENT / 100)
    
    max_overall_percent = (max_discount_allowed_amount / total_price) * 100 if total_price > 0 else 0.0
    max_overall_percent = min(max_overall_percent, AGENT_MAX_DISCOUNT_PERCENT)
    
    final_discount = min(discount, max_overall_percent)
    
    final_total_price = round(total_price * (1 - final_discount / 100), 2)
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
    for product in products:
        order = Order(
            product_id=product.id,
            user_id=user_id,
            discount_applied=final_discount,
            status="pending_payment",
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_link_id=payment_link_id,
            payment_link_url=payment_link_url,
        )
        created = await order_repo.create(order)
        created_order_ids.append(created.id)
        
        await product_repo.update_stock(product.id, product.stock - 1)
        
    try:
        if thread_id:
            from repositories.chat_audit_repository import chat_audit_repo
            await chat_audit_repo.update_state_patch(user_id, thread_id, {
                "order_placed": True,
                "razorpay_id": razorpay_order_id,
                "payment_status": "pending_payment",
                "user_info": {"name": name, "email": email}
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
        "discount_applied": final_discount,
        "capped": discount > max_overall_percent,
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
