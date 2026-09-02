AGENT_MAX_DISCOUNT_PERCENT = 15.0


def apply_sequential_discounts(base_price: float, discount_percents: list[float]) -> float:
    """
    Apply campaign discounts one after another on the remaining price.
    Example: 100 with 10% then 20% -> 100 * 0.9 * 0.8 = 72.
    """
    price = float(base_price)
    for raw in discount_percents:
        pct = max(0.0, min(float(raw or 0.0), 100.0))
        price *= 1.0 - (pct / 100.0)
    return round(max(0.0, price), 2)


def calculate_absolute_max(product, max_discount: float) -> float:
    """Calculates strict mathematical profit cap to never sell below min margin."""
    if product.price <= 0:
        return 0.0
    profit_cap = ((product.price - (product.cost_price * (1 + product.min_profit_margin_percent / 100))) / product.price) * 100
    return round(max(0.0, min(max_discount, profit_cap, AGENT_MAX_DISCOUNT_PERCENT)), 2)


def calculate_next_offer(requested: float, current: float, absolute_max: float, concession_factor: float) -> dict:
    """
    Incremental haggling. Uses exponential decay (decreasing step sizes).
    concession_factor (e.g. 0.3, 0.4, 0.5) decides how much of the REMAINING available
    margin we give away in this round.
    """
    ceiling = round(max(0.0, min(absolute_max, AGENT_MAX_DISCOUNT_PERCENT)), 2)
    current = round(max(0.0, current), 2)
    requested = round(max(0.0, requested), 2)
    
    # Restrict factor between 10% and 100%
    concession_factor = max(0.1, min(concession_factor, 1.0))

    if requested <= current:
        return {
            "accepted": True,
            "counter": current,
            "max_allowed": ceiling,
            "reason": "User asked for less than or equal to the current offer.",
        }
    
    # Calculate decreasing steps
    distance_to_ceiling = ceiling - current
    variable_step = distance_to_ceiling * concession_factor
    
    # Enforce a minimum step of 0.5% so it doesn't get stuck in micro-fractions forever,
    # unless the ceiling is already reached.
    if distance_to_ceiling > 0:
        variable_step = max(0.5, variable_step)
        
    next_offer = round(min(current + variable_step, requested, ceiling), 2)
    
    if next_offer <= current and current >= ceiling:
        return {
            "accepted": False,
            "counter": current,
            "max_allowed": ceiling,
            "reason": f"Already at the maximum agent discount of {ceiling}%.",
        }

    if next_offer >= requested and requested <= ceiling:
        return {
            "accepted": True,
            "counter": next_offer,
            "max_allowed": ceiling,
            "reason": "Requested discount is within this round's step. Accept.",
        }

    return {
        "accepted": False,
        "counter": next_offer,
        "max_allowed": ceiling,
        "reason": f"Countered at {next_offer}%. Call this tool again if the user asks for more (cap {ceiling}%).",
    }
