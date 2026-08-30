# mcp_server/pricing.py
from mcp_server.server import mcp
from services.combo_pricing_engine import combo_pricing_engine
from services.negotiation_service import negotiation_service
from repositories import ProductRepository

product_repo = ProductRepository()

@mcp.tool()
async def calculate_combo_offer(product_ids: list[int]) -> dict:
    """
    Do ya zyada products ka combo price (safe bundle discount) calculate karta hai.
    Agent is tool ko call karke user ko safely discount offer kar sakta hai, 
    bina merchant ko loss karwaye.
    """
    if not product_ids or len(product_ids) < 2:
        return {"success": False, "error": "Combo calculate karne ke liye kam se kam 2 products chahiye."}
        
    products = []
    for pid in product_ids:
        product = await product_repo.get_by_id(pid)
        if product:
            products.append(product)
            
    if len(products) != len(product_ids):
        return {"success": False, "error": "Kuch products database mein nahi mile."}
        
    # Tumhari service ko call kar raha hai
    result = combo_pricing_engine.calculate_combo_price(products)
    result["success"] = True
    return result


@mcp.tool()
async def negotiate_discount(
    user_id: int,
    cart_items: list[dict],
    current_discount_percent: float,
    requested_discount_percent: float,
    is_angry: bool = False,
) -> dict:
    """
    Pure negotiation calculator — yeh tool khud koi state store nahi karta.
    Agent ko khud apni memory mein pichhla offer (current_discount_percent) rakhna
    hoga aur har negotiation round mein yahan bhejna hoga (pehli baar 0 bhejo).
    cart_items agent ko get_cart se already mila hua hoga, format:
    [{"product_id": 12, "quantity": 1}, ...]
    Response ka counter_offer_percent agent ko apni memory mein update karke
    rakhna hoga taaki agli baar negotiation round mein wahi current_discount_percent
    ki tarah bheje.
    """
    if not cart_items:
        return {"success": False, "error": "cart_items khali hai — negotiate karne se pehle get_cart se cart lo."}

    products = []
    for item in cart_items:
        p = await product_repo.get_by_id(item["product_id"])
        if p:
            products.append(p)

    if not products:
        return {"success": False, "error": "cart_items ke products database mein nahi mile."}

    result = await negotiation_service.evaluate_combo_negotiation(
        user_id=user_id,
        cart_products=products,
        requested_discount=requested_discount_percent,
        current_discount=current_discount_percent,
        is_angry=is_angry,
    )

    combo = combo_pricing_engine.calculate_combo_price(products)
    combo["effective_discount_percent"] = result["counter_offer_percent"]
    combo["final_price"] = round(combo["subtotal"] * (1 - result["counter_offer_percent"] / 100), 2)

    return {
        "success": True,
        "accepted": result["accepted"],
        "counter_offer_percent": result["counter_offer_percent"],
        "combo_offer": combo,
    }