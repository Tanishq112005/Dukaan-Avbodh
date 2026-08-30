from services.recommendation_service import recommendation_service
from services.combo_pricing_engine import combo_pricing_engine
from repositories.product_repository import ProductRepository

product_repo = ProductRepository()

class UpsellService:
    """
    Orchestrator Service:
    Pehle yeh Recommendation Service ko call karta hai best product nikalne ke liye.
    Phir yeh us product ko user ke cart ke saath jod kar Combo Pricing Engine ko bhejta hai.
    """
    
    async def generate_upsell_offer(self, user_id: int, cart_items: list[dict]) -> dict:
        # 1. Get Recommendations from pure Recommendation Service
        suggested_products = await recommendation_service.get_best_suggestion(user_id, cart_items)
        
        if not suggested_products:
            return {"success": False, "message": "No suitable recommendations found."}
            
        # 2. Fetch actual Product models for Cart Items
        cart_products = []
        for item in cart_items:
            p_id = item.get("id")
            if p_id:
                p = await product_repo.get_by_id(p_id)
                if p:
                    cart_products.append(p)
                    
        # 3. Create the combo list using the FIRST suggestion for future use
        # (Though we won't show it immediately based on new rules)
        best_product = suggested_products[0]
        combo_list = cart_products + [best_product]
        
        # 4. Generate bounded pricing from Combo Pricing Engine
        combo_offer = combo_pricing_engine.calculate_combo_price(combo_list)
        
        return {
            "success": True,
            "suggested_products": [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in suggested_products],
            "combo_offer": combo_offer
        }

upsell_service = UpsellService()
