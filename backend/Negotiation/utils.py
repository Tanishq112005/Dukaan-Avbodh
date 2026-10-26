from typing import List, Any, Dict, Union

AGENT_MAX_DISCOUNT_PERCENT = 15.0


def _extract_item_fields(item: Any) -> tuple[float, float, float, int]:
    """Helper to extract (cost_price, price, min_profit_margin_percent, quantity) from various item types."""
    if isinstance(item, dict):
        cost = float(item.get("cost_price", 0.0) or 0.0)
        price = float(item.get("price", item.get("selling_price", 0.0)) or 0.0)
        margin = float(item.get("min_profit_margin_percent", 0.0) or 0.0)
        qty = int(item.get("quantity", 1) or 1)
    else:
        cost = float(getattr(item, "cost_price", 0.0) or 0.0)
        price = float(getattr(item, "price", getattr(item, "selling_price", 0.0)) or 0.0)
        margin = float(getattr(item, "min_profit_margin_percent", 0.0) or 0.0)
        qty = int(getattr(item, "quantity", 1) or 1)

    return cost, price, max(0.0, margin), max(1, qty)


def calculate_discount_limits(items: List[Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive profit, cost, and discount limits across a list of items.

    Formula:
      - min_selling_price_per_unit = cost_price + (cost_price * min_profit_margin_percent / 100)
      - total_minimum_selling_price = sum(min_selling_price_per_unit * quantity)
      - total_selling_price = sum(price * quantity)
      - total_cost_price = sum(cost_price * quantity)
      - max_discount_amount = total_selling_price - total_minimum_selling_price
      - max_discount_percentage = (max_discount_amount / total_selling_price) * 100
    """
    if not items:
        return {
            "total_selling_price": 0.0,
            "total_cost_price": 0.0,
            "total_minimum_selling_price": 0.0,
            "max_discount_amount": 0.0,
            "max_discount_percentage": 0.0,
            "is_loss_leader": False,
        }

    total_selling_price = 0.0
    total_cost_price = 0.0
    total_minimum_selling_price = 0.0

    for item in items:
        cost, price, margin, qty = _extract_item_fields(item)
        min_unit_selling = cost + ((cost * margin) / 100.0)

        total_selling_price += price * qty
        total_cost_price += cost * qty
        total_minimum_selling_price += min_unit_selling * qty

    # Financial margin checks
    is_loss_leader = total_selling_price <= total_cost_price
    max_discount_amount = max(0.0, total_selling_price - total_minimum_selling_price)

    if total_selling_price <= 0 or total_selling_price <= total_minimum_selling_price:
        max_discount_pct = 0.0
    else:
        max_discount_pct = (max_discount_amount / total_selling_price) * 100.0

    return {
        "total_selling_price": round(total_selling_price, 2),
        "total_cost_price": round(total_cost_price, 2),
        "total_minimum_selling_price": round(total_minimum_selling_price, 2),
        "max_discount_amount": round(max_discount_amount, 2),
        "max_discount_percentage": round(max_discount_pct, 2),
        "is_loss_leader": is_loss_leader,
    }


def calculate_product_discount_limits(product: Any) -> Dict[str, Any]:
    """
    Calculate profit margins and maximum allowable discount percentage for an individual product.
    Respects:
      1. Minimum required merchant profit margin (cost_price * min_profit_margin_percent).
      2. Product-specific discount limit if configured by merchant (product.discount).
      3. Hard system ceiling (AGENT_MAX_DISCOUNT_PERCENT = 15%).
    """
    cost, price, margin, _ = _extract_item_fields(product)
    product_discount_ceiling = float(getattr(product, "discount", 0.0) or 0.0)

    min_unit_selling = cost + ((cost * margin) / 100.0)
    is_loss_leader = price <= cost

    if price <= 0 or price <= min_unit_selling:
        margin_max_pct = 0.0
    else:
        margin_max_pct = ((price - min_unit_selling) / price) * 100.0

    # Determine absolute allowed ceiling
    if product_discount_ceiling > 0:
        allowed_ceiling = min(margin_max_pct, product_discount_ceiling, AGENT_MAX_DISCOUNT_PERCENT)
    else:
        allowed_ceiling = min(margin_max_pct, AGENT_MAX_DISCOUNT_PERCENT)

    allowed_ceiling = round(max(0.0, allowed_ceiling), 2)
    max_discount_amount = round(price * (allowed_ceiling / 100.0), 2)
    min_selling_price = round(price - max_discount_amount, 2)

    return {
        "price": round(price, 2),
        "cost_price": round(cost, 2),
        "min_profit_margin_percent": round(margin, 2),
        "min_selling_price": min_selling_price,
        "max_discount_amount": max_discount_amount,
        "max_discount_percentage": allowed_ceiling,
        "product_configured_discount": product_discount_ceiling,
        "is_loss_leader": is_loss_leader,
    }


def maximumDiscountPossible(itemsList: List[Any]) -> float:
    """
    Calculate the maximum discount percentage possible across the items in the cart
    without breaching the merchant's required minimum profit margin.
    """
    limits = calculate_discount_limits(itemsList)
    return limits["max_discount_percentage"]


def calculate_next_offer(
    requested: float,
    current: float,
    absolute_max: float,
    concession_factor: float = 0.40,
) -> Dict[str, Any]:
    """
    Haggling step calculator using diminishing returns.
    concession_factor determines how much of the remaining margin to concede per round.
    Default 0.40 treats every customer with loyal-tier concession.
    """
    ceiling = round(max(0.0, absolute_max), 2)
    current = round(max(0.0, current), 2)
    requested = round(max(0.0, requested), 2)
    factor = max(0.1, min(concession_factor, 1.0))

    if requested <= current:
        return {
            "accepted": True,
            "counter": current,
            "max_allowed": ceiling,
            "reason": "Requested discount is less than or equal to current offered discount.",
        }

    distance_to_ceiling = ceiling - current
    if distance_to_ceiling <= 0:
        return {
            "accepted": False,
            "counter": current,
            "max_allowed": ceiling,
            "reason": f"Already at the maximum possible discount of {ceiling}%.",
        }

    variable_step = max(0.5, distance_to_ceiling * factor)
    next_offer = round(min(current + variable_step, requested, ceiling), 2)

    if next_offer >= requested and requested <= ceiling:
        return {
            "accepted": True,
            "counter": next_offer,
            "max_allowed": ceiling,
            "reason": f"Requested discount of {requested}% is within acceptable range. Accepted.",
        }

    return {
        "accepted": False,
        "counter": next_offer,
        "max_allowed": ceiling,
        "reason": f"Counter-offered at {next_offer}%. Requested was {requested}%, maximum possible is {ceiling}%.",
    }


def calculate_product_next_offer(
    product: Any,
    requested_discount_percent: float,
    current_discount_percent: float = 0.0,
    concession_factor: float = 0.40,
) -> Dict[str, Any]:
    """
    Step-by-step negotiation calculator for an individual product.
    Computes diminishing return counter-offers strictly bounded by product economics.
    """
    limits = calculate_product_discount_limits(product)
    ceiling = limits["max_discount_percentage"]

    if limits["is_loss_leader"] or limits["price"] <= 0:
        return {
            "accepted": False,
            "next_discount_percent": 0.0,
            "counter_offer_price": limits["price"],
            "original_price": limits["price"],
            "absolute_max_discount_percent": 0.0,
            "reason": "Product price is at or below cost price. No discount can be offered.",
        }

    result = calculate_next_offer(
        requested=requested_discount_percent,
        current=current_discount_percent,
        absolute_max=ceiling,
        concession_factor=concession_factor,
    )

    counter_discount = result["counter"]
    counter_price = round(limits["price"] * (1.0 - counter_discount / 100.0), 2)

    # Financial floor check: price must stay strictly above cost
    if counter_price <= limits["cost_price"]:
        counter_price = round(limits["cost_price"] + 0.01, 2)
        result["accepted"] = False
        if limits["price"] > 0:
            counter_discount = round(max(0.0, (1.0 - counter_price / limits["price"]) * 100.0), 2)
        result["reason"] = "Counter discount clipped to protect base cost."

    return {
        "accepted": result["accepted"],
        "next_discount_percent": counter_discount,
        "counter_offer_price": counter_price,
        "original_price": limits["price"],
        "absolute_max_discount_percent": ceiling,
        "reason": result["reason"],
    }
