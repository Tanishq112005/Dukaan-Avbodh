# services/combo_pricing_engine.py
from models import Product


class ComboPricingEngine:
    """
    Do (ya zyada) products ko combo mein safely price karta hai —
    merchant ka minimum profit margin kabhi cross nahi hota, chahe kitna bhi discount stack ho.
    """

    COMBO_BONUS_PERCENT = 5.0   # combo lene pe extra thoda discount

    def calculate_combo_price(self, products: list[Product]) -> dict:
        subtotal = sum(p.price for p in products)

        individual_discounted_total = sum(
            p.price * (1 - (p.discount / 100)) for p in products
        )

        # Safe floor ab sirf cost_price nahi, cost_price + guaranteed minimum profit hai
        safe_floor = sum(
            p.cost_price * (1 + p.min_profit_margin_percent / 100) for p in products
        )

        combo_price = individual_discounted_total * (1 - self.COMBO_BONUS_PERCENT / 100)

        final_price = max(combo_price, safe_floor)   # yeh line ab profit-protected hai, sirf loss-protected nahi

        effective_discount_percent = ((subtotal - final_price) / subtotal) * 100 if subtotal > 0 else 0
        was_floor_capped = combo_price < safe_floor

        # Actual profit calculate karo — transparency/audit ke liye
        total_cost = sum(p.cost_price for p in products)
        actual_profit = final_price - total_cost
        actual_profit_percent = (actual_profit / total_cost * 100) if total_cost > 0 else 0

        return {
            "subtotal": round(subtotal, 2),
            "final_price": round(final_price, 2),
            "effective_discount_percent": round(effective_discount_percent, 2),
            "floor_protected": was_floor_capped,
            "merchant_profit": round(actual_profit, 2),
            "merchant_profit_percent": round(actual_profit_percent, 2),
            "products": [p.name for p in products]
        }


combo_pricing_engine = ComboPricingEngine()