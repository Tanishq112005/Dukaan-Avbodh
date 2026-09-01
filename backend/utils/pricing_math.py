def calculate_absolute_max(product, max_discount: float) -> float:
    """Calculates strict mathematical profit cap to never sell below min margin."""
    if product.price <= 0: return 0.0
    profit_cap = ((product.price - (product.cost_price * (1 + product.min_profit_margin_percent / 100))) / product.price) * 100
    return round(max(0.0, min(max_discount, profit_cap)), 2)

def calculate_next_offer(requested: float, current: float, absolute_max: float, step: float) -> dict:
    if requested <= current:
        return {"accepted": True, "counter": current, "reason": "User asked for less/same discount."}
    if requested > absolute_max:
        next_offer = round(min(current + step, absolute_max), 2)
        if next_offer <= current:
            return {"accepted": False, "counter": current, "reason": f"Hit strict margin limit. Cannot exceed {absolute_max}%."}
        return {"accepted": False, "counter": next_offer, "reason": f"Requested {requested}% is too high. Countering with {next_offer}%."}
    return {"accepted": True, "counter": requested, "reason": "Requested discount is within limits. Accept."}
