from typing import List, Optional
from mcp_server.server import mcp
from repositories import OrderRepository, UserRepository, ProductRepository, DiscountPolicyRepository
from models import Order
from config.database import db_connection
from sqlmodel import select
from models.user import User
import os
import razorpay
order_repo = OrderRepository()
user_repo = UserRepository()
product_repo = ProductRepository()
discount_repo = DiscountPolicyRepository()


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TWV2ichCwzRcvo")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "9Ew8lMz1DUumk4hYVPBbf4dd")

try:
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    rzp_client = None


@mcp.tool()
async def create_order(
    user_id: int, 
    product_ids: List[int], 
    name: str, 
    email: str, 
    address: str, 
    discount: float = 0.0
) -> dict:
    """
    Creates a new order for multiple products, applies bounded discounts, and generates a Razorpay payment link.
    
    LLM Instructions:
    - BEFORE calling this tool, you MUST ask the user (or Buyer Agent) for their delivery name, email, and address.
    - Do not call this tool until you have collected all three pieces of information.
    - Call this tool after the user confirms their cart contents and provides their details.
    - Pass the user_id, product_ids, name, email, address, and the negotiated 'discount' percentage (float).
    - When you receive the response, ALWAYS share the 'payment_link' URL with the user so they can pay.
    """
    # 1. Ensure user exists in the database
    await user_repo.ensure_guest_exists(user_id)
    
    # Update the user's details with the provided name, email, and address
    async with db_connection.get_session() as session:
        user = (await session.exec(select(User).where(User.id == user_id))).first()
        if user:
            user.name = name
            user.identifier = email # Using identifier as email for B2C, or storing it safely
            user.address = address
            session.add(user)
            await session.commit()
    
    products = []
    total_price = 0.0
    max_discount_allowed_amount = 0.0
    
    # 2. Check stock and calculate maximum allowed discount across all products
    for pid in product_ids:
        product = await product_repo.get_by_id(pid)
        if not product or product.stock <= 0:
            return {"success": False, "reason": f"Product ID {pid} is out of stock or does not exist."}
        
        products.append(product)
        total_price += product.price
        
        # Aggregate the maximum allowed discount in currency based on policies
        policy = await discount_repo.get_for_product(pid)
        if policy:
            max_discount_allowed_amount += (product.price * policy.max_discount_percent / 100)
    
    # Calculate the max overall percentage we can allow for this whole cart
    max_overall_percent = (max_discount_allowed_amount / total_price) * 100 if total_price > 0 else 0.0
    
    # Bound the LLM's requested discount by the maximum allowed by policy
    final_discount = min(discount, max_overall_percent)
    
    # Calculate final price in INR
    final_total_price = round(total_price * (1 - final_discount / 100), 2)
    final_amount_paise = int(final_total_price * 100)

    # GRACEFUL FAILURE HANDLING & RAZORPAY INTEGRATION (Hackathon Requirement)
    payment_link_url = None
    razorpay_order_id = None
    
    if rzp_client and final_amount_paise >= 100: # Razorpay minimum is 1 INR (100 paise)
        try:
            # First, create a standard Razorpay Order (Audit Trail Requirement)
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
            
            # Second, generate a Payment Link for Conversational Checkout (Conversational Requirement)
            pl_response = rzp_client.payment_link.create({
                "amount": final_amount_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": "Dukaan AI Shopping Agent Order",
                "customer": {
                    "name": name,
                    "email": email,
                },
                "notify": {
                    "email": True
                },
                "reminder_enable": True,
                "notes": {
                    "order_id": razorpay_order_id
                }
            })
            payment_link_url = pl_response.get("short_url")
            
        except Exception as e:
            # Graceful Failure: If API is down or keys are invalid, we handle it smoothly without crashing
            print(f"[RAZORPAY ERROR] Failed to create payment link: {e}")
            return {
                "success": False,
                "error": "I am so sorry, but our payment gateway (Razorpay) is temporarily down. Your cart is saved securely. Can we try again in a few minutes?"
            }

    # 3. Create internal orders and update stock
    created_order_ids = []
    for product in products:
        order = Order(
            product_id=product.id,
            user_id=user_id,
            discount_applied=final_discount,
            status="confirmed"
        )
        created = await order_repo.create(order)
        created_order_ids.append(created.id)
        
        # Deduct stock
        await product_repo.update_stock(product.id, product.stock - 1)

    return {
        "success": True,
        "order_ids": created_order_ids,
        "razorpay_order_id": razorpay_order_id,
        "payment_link": payment_link_url or "Payment Link Unavailable (API Error)",
        "requested_discount": discount,
        "discount_applied": final_discount,
        "capped": discount > max_overall_percent,
        "total_price_before_discount": round(total_price, 2),
        "final_total_price": final_total_price
    }