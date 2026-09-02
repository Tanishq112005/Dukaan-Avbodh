from mcp_server.server import mcp
from services.combo_pricing_engine import combo_pricing_engine
from services.negotiation_service import negotiation_service
from services.audit_logger import audit_logger
from repositories.cart_repository import cart_repository

@mcp.tool()
async def calculate_combo_offer(user_id: int, discount_percent: float = 0.0) -> dict:
    """
    Retrieves the cart contents and calculates the bundle offer based on a specific discount percentage.
    
    LLM Instructions:
    - DO pass the 'user_id' and the agreed 'discount_percent'. 
    - If you just want to check the base price without any discount, pass 0.0.
    - The backend will automatically fetch the cart items and apply the requested discount percentage to the total selling price.
    - DO use this tool's response to tell the user their exact savings ('discount_amount').
    - DO NOT negotiate if this tool returns an error. Inform the user that combo offers require at least 2 items.
    """
    
    
    cart_items = await cart_repository.get_cart_items(user_id)
    
    total_items = sum(item["quantity"] for item in cart_items)
    
    if not cart_items or total_items < 2:
        return {"success": False, "error": "Cart must have at least 2 items to calculate a combo offer."}
        
    # Calculate subtotal directly from cart items (Selling Price)
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    
    # Apply the provided discount percentage
    discount_amount = round(subtotal * (discount_percent / 100), 2)
    final_price = round(subtotal - discount_amount, 2)
    
    # Clean dictionary to pass back to the LLM
    safe_combo = {
        "subtotal": round(subtotal, 2),
        "final_price": final_price,
        "effective_discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "total_items": total_items,
        "products": [{"id": p.get("id") or p.get("product_id"), "name": p.get("name"), "image": p.get("image_url")} for p in cart_items]
    }
    
    return {
        "success": True,
        "combo_offer": safe_combo
    }
    
    
@mcp.tool()
async def negotiate_discount(
    user_id: int,
    current_discount_percent: float,
    requested_discount_percent: float ,
    thread_id : str = ""
) -> dict:
    """
    Evaluates a user's requested discount against dynamic safety margins and loyalty scores.
    
    LLM Instructions:
    - DO pass the 'user_id', 'current_discount_percent', and 'requested_discount_percent'. 
    - DO pass 'current_discount_percent' as 0.0 if this is the very first round of negotiation.
    - Call this tool AGAIN every time the user asks for a different / higher discount. Never invent the next percentage yourself.
    - IF 'accepted' is True, confirm the deal with the user at the 'counter_offer_percent'.
    - IF 'accepted' is False, politely reject the user's request and make a counter-offer using ONLY the 'counter_offer_percent' returned by this tool.
    - DO NOT reveal internal reasoning, mathematical limits, or maximum possible discounts to the user.
    - DO update your internal memory with the new 'counter_offer_percent' to use as the 'current_discount_percent' for the next round.
    """
    
    # 1. Evaluate logic and fetch cart automatically inside the service
    result  = await negotiation_service.evaluate_combo_negotiation(
        user_id=user_id,
        requested_discount=requested_discount_percent,
        current_discount=current_discount_percent
    )

    
    
    # Extract product info safely
    product_meta = []
    if result.get("products"):
        for p in result["products"]:
            product_meta.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "image_url": p.image_url
            })
            
    await audit_logger.log_action(
        action="negotiate_discount",
        reason=f"User requested {requested_discount_percent}%, current offer {current_discount_percent}%, accepted: {result.get('accepted', False)}, max_allowed: {result.get('absolute_max_discount_percent', 0.0)}%, step_size: {result.get('step_size', 0.0)}%, cost_price: {result.get('total_cart_cost', 0.0)}, min_profit: {result.get('total_cart_min_profit', 0.0)}, max_discount_amount: {result.get('max_discount_amount', 0.0)}, previous_recent: {result.get('user_orders_recent', False)}",
        result=f"Requested: {requested_discount_percent}%, Counter: {result.get('counter_offer_percent', 0.0)}%, Accepted: {result.get('accepted', False)}",
        user_id=user_id,
        thread_id=str(thread_id),
        metadata={"products": product_meta} if product_meta else None
    )
    
    # Save to Chat Audit Repository
    from repositories.chat_audit_repository import chat_audit_repo
    await chat_audit_repo.append_negotiation_log(user_id, str(thread_id), {
        "requested": requested_discount_percent,
        "agent_offered": result.get("counter_offer_percent", 0.0),
        "accepted": result.get("accepted", False)
    })
    
    # Also update static metrics like cost price
    await chat_audit_repo.update_state_patch(user_id, str(thread_id), {
        "cart_products": product_meta,
        "max_discount_we_can_give": result.get('absolute_max_discount_percent', 0.0),
        "total_cost_price": result.get('total_cart_cost', 0.0),
        "total_selling_price": result.get('total_cart_price', 0.0)
    })

    if not result.get("products"):
        return {"success": False, "error": result["agent_internal_reasoning"]}

    # 2. Calculate final combo pricing based on the allowed counter offer
    combo = combo_pricing_engine.calculate_combo_price(result["products"])
    combo["effective_discount_percent"] = result["counter_offer_percent"]
    combo["final_price"] = round(combo["subtotal"] * (1 - result["counter_offer_percent"] / 100), 2)

    return {
        "success": True,
        "accepted": result["accepted"],
        "counter_offer_percent": result["counter_offer_percent"],
        "combo_offer": combo,
    }