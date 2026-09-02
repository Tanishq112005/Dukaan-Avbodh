AGENT_MAX_DISCOUNT_PERCENT = 5.0


def calculate_absolute_max(product, max_discount: float) -> float:
    """Calculates strict mathematical profit cap to never sell below min margin."""
    if product.price <= 0:
        return 0.0
    profit_cap = ((product.price - (product.cost_price * (1 + product.min_profit_margin_percent / 100))) / product.price) * 100
    return round(max(0.0, min(max_discount, profit_cap, AGENT_MAX_DISCOUNT_PERCENT)), 2)


def calculate_next_offer(requested: float, current: float, absolute_max: float, step: float) -> dict:
    """
    Incremental haggling. Each tool call may raise the offer by at most `step`,
    never above the agent ceiling (5%) or the product/combo profit cap.
    A new user ask MUST trigger another call to get the next step.
    """
    ceiling = round(max(0.0, min(absolute_max, AGENT_MAX_DISCOUNT_PERCENT)), 2)
    current = round(max(0.0, current), 2)
    requested = round(max(0.0, requested), 2)
    step = max(0.5, step)

    if requested <= current:
        return {
            "accepted": True,
            "counter": current,
            "max_allowed": ceiling,
            "reason": "User asked for less than or equal to the current offer.",
        }

    next_offer = round(min(current + step, requested, ceiling), 2)

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
