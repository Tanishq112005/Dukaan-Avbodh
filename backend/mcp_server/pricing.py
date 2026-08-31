from mcp_server.server import mcp
from services.combo_pricing_engine import combo_pricing_engine
from services.negotiation_service import negotiation_service

@mcp.tool()
async def calculate_combo_offer(user_id: int) -> dict:
    """
    Retrieves the cart contents and calculates the total base selling price (subtotal).
    
    LLM Instructions:
    - DO pass ONLY the user_id. The backend will automatically fetch the cart items.
    - DO use this tool to check the base total price before starting any bundle or combo negotiations.
    - DO NOT negotiate if this tool returns an error (e.g., if the cart has fewer than 2 items). Inform the user that combo offers require at least 2 items.
    """
    from repositories.cart_repository import cart_repository
    
    cart_items = await cart_repository.get_cart_items(user_id)
    
    total_items = sum(item["quantity"] for item in cart_items)
    
    if not cart_items or total_items < 2:
        return {"success": False, "error": "Cart must have at least 2 items to calculate a combo offer."}
        
    # Simply returning the sum of selling prices (price * quantity)
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    
    return {
        "success": True,
        "subtotal_selling_price": round(subtotal, 2),
        "total_items": total_items
    }
    
    
@mcp.tool()
async def negotiate_discount(
    user_id: int,
    current_discount_percent: float,
    requested_discount_percent: float
) -> dict:
    """
    Evaluates a user's requested discount against dynamic safety margins and loyalty scores.
    
    LLM Instructions:
    - DO pass the 'user_id', 'current_discount_percent', and 'requested_discount_percent'. 
    - DO pass 'current_discount_percent' as 0.0 if this is the very first round of negotiation.
    - IF 'accepted' is True, confirm the deal with the user at the 'counter_offer_percent'.
    - IF 'accepted' is False, politely reject the user's request and make a counter-offer using ONLY the 'counter_offer_percent' returned by this tool.
    - DO NOT reveal internal reasoning, mathematical limits, or maximum possible discounts to the user.
    - DO update your internal memory with the new 'counter_offer_percent' to use as the 'current_discount_percent' for the next round.
    """
    
    # 1. Evaluate logic and fetch cart automatically inside the service
    result = await negotiation_service.evaluate_combo_negotiation(
        user_id=user_id,
        requested_discount=requested_discount_percent,
        current_discount=current_discount_percent
    )

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