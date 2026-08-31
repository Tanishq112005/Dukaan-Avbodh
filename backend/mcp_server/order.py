from typing import List
from mcp_server.server import mcp
from repositories import OrderRepository, UserRepository, ProductRepository, DiscountPolicyRepository
from models import Order

order_repo = OrderRepository()
user_repo = UserRepository()
product_repo = ProductRepository()
discount_repo = DiscountPolicyRepository()


@mcp.tool()
async def create_order(user_id: int, product_ids: List[int], discount: float = 0.0) -> dict:
    """
    Creates a new order for multiple products and applies a bounded discount.
    
    LLM Instructions:
    - Call this tool after the user confirms their cart contents for purchase.
    - Pass the user_id, an array of product_ids from the cart, and the negotiated 'discount' percentage (float).
    - If the user did not negotiate a discount, pass 0.0.
    """
    # 1. Ensure user exists in the database
    await user_repo.ensure_guest_exists(user_id)
    
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

    # 3. Create orders and update stock
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
        "requested_discount": discount,
        "discount_applied": final_discount,
        "capped": discount > max_overall_percent,
        "total_price_before_discount": round(total_price, 2),
        "final_total_price": round(total_price * (1 - final_discount / 100), 2)
    }