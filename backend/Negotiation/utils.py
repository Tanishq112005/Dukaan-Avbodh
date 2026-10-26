from typing import List, Any, Dict, Union

AGENT_MAX_DISCOUNT_PERCENT = 15.0


def _extract_item_fields(item: Any) -> tuple[float, float, float, int]:
    """Helper to extract (cost_price, price, min_profit_margin_percent, quantity) from various item types."""
    from Product.models import get_base_selling_price

    if isinstance(item, dict):
        cost = float(item.get("cost_price", 0.0) or 0.0)
        if item.get("original_price") is not None and float(item["original_price"]) > 0:
            price = float(item["original_price"])
        else:
            price = get_base_selling_price(item)
        margin = float(item.get("min_profit_margin_percent", 0.0) or 0.0)
        qty = int(item.get("quantity", 1) or 1)
    else:
        cost = float(getattr(item, "cost_price", 0.0) or 0.0)
        if getattr(item, "original_price", None) is not None and float(item.original_price) > 0:
            price = float(item.original_price)
        else:
            price = get_base_selling_price(item)
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


def calculate_cart_discount_headroom(detailed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes total cart economics taking into account the current selling price of each product
    after its individual discount, its wholesale cost price, and required minimum profit margins.

    Returns:
      - total_original_price: Sum of original listing prices across all cart items.
      - current_cart_total: Sum of current selling prices after each product's discount.
      - total_cost_price: Sum of wholesale cost prices.
      - total_minimum_selling_price: Sum of minimum allowable selling prices across all items.
      - current_effective_discount_pct: Overall discount % already active on the cart.
      - max_discount_percentage: Maximum allowable overall discount % from original price.
      - absolute_max_ceiling: Upper limit bounded by AGENT_MAX_DISCOUNT_PERCENT (15%).
      - is_loss_leader: True if current cart total is at or below cost.
    """
    if not detailed_items:
        return {
            "total_original_price": 0.0,
            "current_cart_total": 0.0,
            "total_cost_price": 0.0,
            "total_minimum_selling_price": 0.0,
            "current_effective_discount_pct": 0.0,
            "max_discount_percentage": 0.0,
            "absolute_max_ceiling": 0.0,
            "is_loss_leader": False,
        }

    total_original_price = 0.0
    current_cart_total = 0.0
    total_cost_price = 0.0
    total_minimum_selling_price = 0.0

    for item in detailed_items:
        qty = max(1, int(item.get("quantity", 1) or 1))
        orig_price = float(item.get("original_price") or item.get("price") or 0.0)
        curr_price = float(item.get("current_price") or item.get("discounted_price") or orig_price)
        cost = float(item.get("cost_price", 0.0) or 0.0)
        margin = float(item.get("min_profit_margin_percent", 0.0) or 0.0)

        # Minimum required unit selling price to protect profit margin
        min_unit_margin = cost + ((cost * margin) / 100.0)

        # Check product-level ceiling if available
        product = item.get("product")
        p_disc_ceiling = float(getattr(product, "discount", 0.0) or item.get("discount", 0.0) or 0.0)
        if p_disc_ceiling > 0:
            min_unit_ceiling = orig_price * (1.0 - p_disc_ceiling / 100.0)
            safe_unit_floor = max(min_unit_margin, min_unit_ceiling)
        else:
            safe_unit_floor = min_unit_margin

        # Floor must never go below cost
        safe_unit_floor = max(safe_unit_floor, cost + 0.01)
        if orig_price > 0:
            safe_unit_floor = min(safe_unit_floor, orig_price)

        total_original_price += orig_price * qty
        current_cart_total += curr_price * qty
        total_cost_price += cost * qty
        total_minimum_selling_price += safe_unit_floor * qty

    is_loss_leader = current_cart_total <= total_cost_price

    if total_original_price > 0:
        current_effective_discount_pct = round(
            max(0.0, (total_original_price - current_cart_total) / total_original_price * 100.0), 2
        )
        max_possible_discount_amount = max(0.0, total_original_price - total_minimum_selling_price)
        max_discount_pct = (max_possible_discount_amount / total_original_price) * 100.0
    else:
        current_effective_discount_pct = 0.0
        max_discount_pct = 0.0

    absolute_max_ceiling = round(min(max(0.0, max_discount_pct), AGENT_MAX_DISCOUNT_PERCENT), 2)

    return {
        "total_original_price": round(total_original_price, 2),
        "current_cart_total": round(current_cart_total, 2),
        "total_cost_price": round(total_cost_price, 2),
        "total_minimum_selling_price": round(total_minimum_selling_price, 2),
        "current_effective_discount_pct": current_effective_discount_pct,
        "max_discount_percentage": round(max_discount_pct, 2),
        "absolute_max_ceiling": absolute_max_ceiling,
        "is_loss_leader": is_loss_leader,
    }
