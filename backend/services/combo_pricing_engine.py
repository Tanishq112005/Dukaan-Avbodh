# services/combo_pricing_engine.py
from models import Product


class ComboPricingEngine:
    """
    Do (ya zyada) products ko combo mein safely price karta hai —
    merchant ka minimum profit margin kabhi cross nahi hota, chahe kitna bhi discount stack ho.
    """

    COMBO_BONUS_PERCENT = 5.0   # combo lene pe extra thoda discount

        
    def get_negotiation_limits(self, products: list[Product]) -> dict:
        """
        Returns the mathematical limits for a combo, exactly defining the available 
        discount pool (playable amount) before hitting merchant's minimum profit.
        """
        total_price = sum(p.price for p in products)
        total_cost = sum(p.cost_price for p in products)
        total_min_profit = sum(p.cost_price * (p.min_profit_margin_percent / 100) for p in products)
        
        max_discount_amount = total_price - total_cost - total_min_profit
        absolute_max_discount_percent = (max_discount_amount / total_price) * 100 if total_price > 0 else 0.0
        absolute_max_discount_percent = max(0.0, absolute_max_discount_percent)
        
        return {
            "total_price": total_price,
            "total_cost": total_cost,
            "total_min_profit": total_min_profit,
            "max_discount_amount": max_discount_amount,
            "absolute_max_discount_percent": absolute_max_discount_percent
        }

    def calculate_combo_price(self, products: list[Product]) -> dict:
        """
        Calculates the subtotal and base combo details for a list of products.
        Does not apply any custom discount by default.
        """
        if not products:
            return {
                "subtotal": 0.0,
                "final_price": 0.0,
                "effective_discount_percent": 0.0,
                "discount_amount": 0.0,
                "total_items": 0,
                "products": []
            }
            
        subtotal = sum(p.price for p in products)
        
        return {
            "subtotal": round(subtotal, 2),
            "final_price": round(subtotal, 2),
            "effective_discount_percent": 0.0,
            "discount_amount": 0.0,
            "total_items": len(products),
            "products": [{"id": p.id, "name": p.name, "image": p.image_url} for p in products]
        }

combo_pricing_engine = ComboPricingEngine()