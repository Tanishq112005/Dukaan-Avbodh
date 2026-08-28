# mcp_server/pricing.py
from mcp_server.server import mcp
from services.combo_pricing_engine import combo_pricing_engine
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