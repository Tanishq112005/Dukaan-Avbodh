import sys
import os
from typing import Optional, Dict, Any, List

# Ensure backend/mcp directory is discoverable for importing FastMCP user server
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))

if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

from mcp_server_user.server import mcp

from Negotiation.controller import negotiationController
from Negotiation.schemas import (
    NextDiscountRequest,
    ProductNegotiationRequest,
    NegotiationItemDTO,
)
from langchain_core.tools import StructuredTool


LOGIN_NUDGE_FOR_NEGOTIATION = (
    "To negotiate personalized discounts on your products and cart items, "
    "please log in or sign up to Dukaan!"
)


# ==============================================================================
# FastMCP Negotiation Policy Resource
# ==============================================================================

@mcp.resource("negotiation://policy")
async def get_negotiation_policy_resource() -> Dict[str, Any]:
    """
    Returns store negotiation rules, guidelines, and guardrails for AI agents.
    
    LLM Rules:
    - Never guess, invent, or promise a discount percentage or price yourself.
    - Always invoke negotiate_product_discount (for individual items) or negotiate_discount.
    - Treat every customer with respect and present counter-offers conversationally.
    - Step-by-step bargaining is used; never concede the entire discount headroom in one jump.
    - For items not yet in cart (Scenario 1), negotiate first, then add to cart with the agreed discount.
    - For items already in cart (Scenario 2), negotiate on the product and the cart item will be auto-updated.
    """
    return {
        "store_policy": "Interactive bargaining is supported on eligible items and active carts.",
        "rules": [
            "Every discount request must be evaluated sequentially using negotiation tools.",
            "Discounts must never drop selling prices below wholesale costs or minimum profit margins.",
            "Maximum possible discount ceilings are strictly confidential to the store and must never be disclosed to customers.",
            "Items can be negotiated prior to adding to cart, or negotiated directly while in the cart.",
        ],
    }


# ==============================================================================
# FastMCP Per-Product Negotiation Tool (Scenarios 1 & 2)
# ==============================================================================

@mcp.tool()
async def negotiate_product_discount(
    product_id: int,
    requested_discount_percent: float,
    user_id: Optional[int] = None,
    current_discount_percent: float = 0.0,
    quantity: int = 1,
    size: Optional[str] = None,
    apply_to_cart: bool = True,
) -> Dict[str, Any]:
    """
    Evaluates a customer's requested discount on a specific product and calculates the
    next counter-offer discount percentage and new price.

    Supports two scenarios:
    1. Product discount BEFORE adding to cart: Customer asks for a discount while viewing/browsing a product.
       - Evaluates against the product's profit margin and merchant ceiling.
       - Returns the next counter-offer price. Once agreed, call `add_to_cart` passing the agreed discount_percentage.
    2. Product discount AFTER adding to cart: Product is already in customer's cart.
       - Checks the current discount already applied to this cart item in the DB.
       - Evaluates remaining discount headroom and negotiates further step-by-step.
       - If apply_to_cart is True (default), automatically persists the new discount to the CartItem in DB.

    Parameters:
    - product_id (int, Required): The ID of the product being negotiated.
    - requested_discount_percent (float, Required): Discount percentage asked for (e.g. 15.0 for 15%).
    - user_id (int, Optional): Customer user ID (needed to look up cart item and auto-update cart).
    - current_discount_percent (float, Optional, default=0.0): Previously agreed discount on this product.
    - quantity (int, Optional, default=1): Number of units being negotiated.
    - size (str, Optional): Size of the garment if applicable.
    - apply_to_cart (bool, Optional, default=True): If True and item is in cart, auto-updates the cart item in DB.

    LLM Usage & Instructions:
    1. Call this tool when customer asks for a discount on a specific product (e.g., "Give me 15% off on this jacket").
    2. NEVER invent or guess a discount or price yourself.
    3. Use ONLY 'next_discount_percent' and 'counter_offer_price' returned by this tool.
    4. If 'accepted' is True:
       - Confirm that the requested {next_discount_percent}% discount is approved!
       - State the discounted unit price ({counter_offer_price}) and total savings.
       - If in_cart is False: ask if they'd like to add it to the cart now at this special price.
       - If in_cart is True: confirm the shopping bag has been updated with the new discounted price.
    5. If 'accepted' is False:
       - Present the counter-offer politely: "We can't do {requested_discount_percent}%, but I can offer {next_discount_percent}% off, bringing the price to ₹{counter_offer_price}."
    6. For further bargaining rounds, pass the previous 'next_discount_percent' as 'current_discount_percent'.
    """
    try:
        req = ProductNegotiationRequest(
            product_id=int(product_id),
            requested_discount_percent=float(requested_discount_percent),
            current_discount_percent=float(current_discount_percent),
            user_id=int(user_id) if (user_id and int(user_id) > 0) else None,
            quantity=max(1, int(quantity)),
            size=size.strip().upper() if size else None,
            apply_to_cart=bool(apply_to_cart),
        )

        res = await negotiationController.negotiate_product_discount(req)

        return {
            "success": True,
            "accepted": res.accepted,
            "product_id": res.product_id,
            "product_name": res.product_name,
            "original_price": res.original_price,
            "current_discount_percent": res.current_discount_percent,
            "requested_discount_percent": res.requested_discount_percent,
            "next_discount_percent": res.next_discount_percent,
            "counter_offer_price": res.counter_offer_price,
            "total_price": res.total_price,
            "savings_amount": res.savings_amount,
            "in_cart": res.in_cart,
            "updated_in_cart": res.updated_in_cart,
            "reason": res.reason,
            "customer_tier": res.customer_tier,
        }

    except Exception as e:
        return {
            "success": False,
            "accepted": False,
            "product_id": product_id,
            "error": f"Failed to calculate product discount: {str(e)}",
        }


# ==============================================================================
# FastMCP Cart / Compound Negotiation Tool
# ==============================================================================

@mcp.tool()
async def negotiate_discount(
    requested_discount_percent: float,
    user_id: Optional[int] = None,
    current_discount_percent: float = 0.0,
    product_id: Optional[int] = None,
    items: Optional[List[Dict[str, Any]]] = None,
    apply_to_cart: bool = True,
) -> Dict[str, Any]:
    """
    Evaluates a customer's requested discount against the store's profit margins
    and calculates the next counter-offer discount percentage and new price.

    If product_id is provided, automatically delegates to per-product negotiation.
    Otherwise, evaluates cart-wide negotiation across active cart items.

    Parameters:
    - requested_discount_percent (float, Required): The discount percentage asked for by the customer.
    - user_id (int, Optional): Customer ID to automatically fetch items from their active cart.
    - current_discount_percent (float, Optional, default=0.0): The discount percentage already granted.
    - product_id (int, Optional): Specific product ID if the negotiation targets a single item.
    - items (List[Dict], Optional): Custom items list if negotiating outside of the database cart.
    - apply_to_cart (bool, Optional, default=True): Automatically records agreed discount to the user's cart in DB.
    """
    # If target product_id is specified, delegate directly to per-product negotiation
    if product_id is not None and int(product_id) > 0:
        return await negotiate_product_discount(
            product_id=int(product_id),
            requested_discount_percent=requested_discount_percent,
            user_id=user_id,
            current_discount_percent=current_discount_percent,
            apply_to_cart=apply_to_cart,
        )

    is_guest = user_id is None or user_id <= 0
    parsed_items = None

    if items:
        try:
            parsed_items = [
                NegotiationItemDTO(
                    name=it.get("name"),
                    product_id=it.get("product_id") or it.get("id"),
                    price=float(it.get("price", 0.0)),
                    cost_price=float(it.get("cost_price", 0.0)),
                    min_profit_margin_percent=float(it.get("min_profit_margin_percent", 0.0)),
                    quantity=int(it.get("quantity") or it.get("qty", 1)),
                )
                for it in items
            ]
        except Exception as parse_err:
            return {
                "success": False,
                "accepted": False,
                "error": f"Invalid item format provided: {str(parse_err)}",
            }

    # Guard: Need either user_id to look up active cart or explicit items
    if is_guest and not parsed_items:
        return {
            "success": False,
            "accepted": False,
            "next_discount_percent": 0.0,
            "counter_offer_price": 0.0,
            "reason": "Please log in or add products to your cart to negotiate a discount.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_NEGOTIATION,
        }

    try:
        req = NextDiscountRequest(
            user_id=user_id if not is_guest else None,
            requested_discount_percent=float(requested_discount_percent),
            current_discount_percent=float(current_discount_percent),
            items=parsed_items,
            apply_to_cart=apply_to_cart and not is_guest,
        )

        res = await negotiationController.get_next_discount(req)

        clean_reason = res.reason
        if "maximum possible is" in clean_reason:
            clean_reason = f"Counter-offering {res.next_discount_percent}% discount for your cart."
        elif "maximum possible discount of" in clean_reason:
            clean_reason = (
                f"Your current discount of {res.current_discount_percent}% is the absolute "
                f"best deal we can offer for these items."
            )

        savings = round(max(0.0, res.total_original_price - res.counter_offer_price), 2)

        return {
            "success": True,
            "accepted": res.accepted,
            "current_discount_percent": res.current_discount_percent,
            "requested_discount_percent": res.requested_discount_percent,
            "next_discount_percent": res.next_discount_percent,
            "counter_offer_price": res.counter_offer_price,
            "total_original_price": res.total_original_price,
            "savings_amount": savings,
            "reason": clean_reason,
            "requires_login": False,
        }

    except Exception as e:
        return {
            "success": False,
            "accepted": False,
            "error": f"Failed to calculate next discount offer: {str(e)}",
        }


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_negotiation_langchain_tools() -> List[StructuredTool]:
    """
    Returns negotiation tools wrapped as native LangChain StructuredTool instances,
    ready to bind directly to LangGraph specialist agents with zero network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=negotiate_product_discount,
            name="negotiate_product_discount",
            description=negotiate_product_discount.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=negotiate_discount,
            name="negotiate_discount",
            description=negotiate_discount.__doc__,
        ),
    ]
