# mcp/order.py
from mcp_server.server import mcp
from repositories import OrderRepository, UserRepository, ProductRepository, DiscountPolicyRepository
from models import Order

order_repo = OrderRepository()
user_repo = UserRepository()
product_repo = ProductRepository()
discount_repo = DiscountPolicyRepository()


@mcp.resource("policy://discount/{product_id}")
async def get_discount_policy_info(product_id: int) -> dict:
    """Is product ke liye max allowed discount kya hai, batata hai.
    Agent negotiate karne se pehle isse padh sakta hai."""
    policy = await discount_repo.get_for_product(product_id)
    if not policy:
        return {"max_discount_percent": 0.0, "note": "Is product pe discount policy defined nahi hai"}
    return {
        "max_discount_percent": policy.max_discount_percent,
        "min_qty_for_discount": policy.min_qty_for_discount
    }


@mcp.tool()
async def create_order(product_id: int, buyer_identifier: str, buyer_role: str, requested_discount: float = 0.0) -> dict:
    """Naya order banata hai — discount ko policy ke against bound/gate karta hai."""
    user = await user_repo.get_or_create(
        name=buyer_identifier, role=buyer_role, identifier=buyer_identifier
    )
    product = await product_repo.get_by_id(product_id)
    if not product or product.stock <= 0:
        return {"success": False, "reason": "out_of_stock"}

    policy = await discount_repo.get_for_product(product_id)
    max_discount = policy.max_discount_percent if policy else 0.0
    final_discount = min(requested_discount, max_discount)   # yahi hai "bounded" logic

    order = Order(
        product_id=product.id,
        user_id=user.id,
        discount_applied=final_discount,
        status="confirmed"
    )
    created = await order_repo.create(order)

    return {
        "success": True,
        "order_id": created.id,
        "requested_discount": requested_discount,
        "discount_applied": final_discount,
        "capped": requested_discount > max_discount,   # transparency ke liye — agent ko batao ki cap laga
        "final_price": product.price * (1 - final_discount / 100)
    }