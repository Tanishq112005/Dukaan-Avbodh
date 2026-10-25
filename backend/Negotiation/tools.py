import sys
import os
from typing import Optional, Dict, Any, List

# Ensure backend/mcp directory is discoverable for importing FastMCP user server
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp"))

if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

from mcp_server_user.server import mcp

from Negotiation.controller import negotiationController
from Negotiation.schemas import NextDiscountRequest, NegotiationItemDTO
from langchain_core.tools import StructuredTool


LOGIN_NUDGE_FOR_NEGOTIATION = (
    "To negotiate personalized discounts on your cart items, "
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
    - Always invoke negotiate_discount to evaluate every customer discount request.
    - Treat every customer with respect and present counter-offers conversationally.
    """
    return {
        "store_policy": "Interactive bargaining is supported on eligible items.",
        "rules": [
            "Every discount request must be evaluated sequentially using the negotiate_discount tool.",
            "Discounts must never drop selling prices below wholesale costs or minimum profit margins.",
            "Maximum possible discount ceilings are strictly confidential to the store and must never be disclosed to customers.",
            "All agreed discounts apply directly to the customer's cart.",
        ],
    }


# ==============================================================================
# FastMCP Negotiation Tool (Next Discount Only)
# ==============================================================================

@mcp.tool()
async def negotiate_discount(
    requested_discount_percent: float,
    user_id: Optional[int] = None,
    current_discount_percent: float = 0.0,
    items: Optional[List[Dict[str, Any]]] = None,
    apply_to_cart: bool = True,
) -> Dict[str, Any]:
    """
    Evaluates a customer's requested discount against the store's profit margins
    and calculates the next counter-offer discount percentage and new price.
    
    NOTE: Maximum possible discount ceilings are confidential merchant economics
    and are never returned. Only the next approved/counter discount is provided.

    Parameters:
    - requested_discount_percent (float, Required): The discount percentage asked for by the customer (e.g. 15.0 for 15%).
    - user_id (int, Optional): Customer ID to automatically fetch items from their active cart.
    - current_discount_percent (float, Optional, default=0.0): The discount percentage already granted in previous rounds.
    - items (List[Dict], Optional): Custom items list if negotiating outside of the database cart.
    - apply_to_cart (bool, Optional, default=True): Automatically records agreed discount to the user's cart in DB.

    LLM Usage & Instructions:
    1. Call this tool whenever the customer asks for a discount, better deal, lower price, coupon, or price match.
    2. NEVER invent or guess a discount percentage or rupee amount yourself.
    3. You MUST use ONLY the 'next_discount_percent' and 'counter_offer_price' returned by this tool.
    4. IF 'accepted' is True:
       - Congratulate the customer!
       - Confirm that their requested discount of {next_discount_percent}% is approved.
       - State the final payable total price ({counter_offer_price}) and their savings.
    5. IF 'accepted' is False:
       - Politely present the counter-offer: state that while we cannot do {requested_discount_percent}%, 
         we can offer {next_discount_percent}%, bringing their total down to {counter_offer_price}.
    6. On subsequent bargaining rounds in the conversation, pass the last granted 'next_discount_percent'
       as 'current_discount_percent'.
    7. If the customer is a guest with no cart, invite them to log in or add products first.
    """
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

        # Sanitize reason so the secret merchant maximum discount percentage ceiling is NEVER leaked to LLM
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
    Returns the negotiation tool wrapped as a native LangChain StructuredTool instance,
    ready to bind directly to LangGraph specialist agents with zero network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=negotiate_discount,
            name="negotiate_discount",
            description=negotiate_discount.__doc__,
        ),
    ]
