import sys
import os
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

# Ensure backend directory is discoverable for importing FastMCP user server
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mcp'))
if mcp_path not in sys.path:
    sys.path.insert(0, mcp_path)

try:
    import mcp as _official_mcp
    if hasattr(_official_mcp, '__path__') and mcp_path not in _official_mcp.__path__:
        _official_mcp.__path__.append(mcp_path)
except Exception:
    pass

try:
    from mcp.user.server import mcp
except Exception:
    try:
        from user.server import mcp
    except Exception:
        class DummyMCP:
            def tool(self, *args, **kwargs):
                return lambda fn: fn
            def resource(self, *args, **kwargs):
                return lambda fn: fn
        mcp = DummyMCP()

from Cart.controller import cartController
from Cart.schemas import (
    AddItemRequest,
    UpdateItemRequest,
    UpdateItemDiscountRequest,
    DeleteItemRequest,
)
from UserEvents.models import EventType
from UserEvents.tracker import record_user_event
from langchain_core.tools import StructuredTool


LOGIN_NUDGE_FOR_CART = (
    "To save and view items in your personal shopping cart, "
    "please log in or sign up to Dukaan!"
)


# ==============================================================================
# FastMCP Cart Resources
# ==============================================================================

@mcp.resource("cart://policy")
async def get_cart_policy_resource() -> Dict[str, Any]:
    """
    Returns store cart policies and checkout guidelines for AI agents.
    
    LLM Rules:
    - Adding items to cart verifies real-time stock availability.
    - Size specification is strongly recommended for apparel (e.g. S, M, L for shirts; 30, 32, 34 for jeans).
    - Setting an item's quantity to 0 removes it from the cart.
    - When an item had a previously negotiated discount, pass discount_percentage when adding to cart.
    """
    return {
        "cart_policy": "Real-time stock reservation and size selection.",
        "rules": [
            "Quantities must be positive integers.",
            "Always ask or confirm the desired size before adding clothing to the cart.",
            "Items remain in the customer's cart across active browsing sessions.",
            "Negotiated per-product discounts apply directly to cart items.",
        ],
    }


@mcp.resource("cart://supported-sizes")
async def get_supported_sizes_resource() -> Dict[str, Any]:
    """
    Returns the standard supported size values for apparel products in Dukaan.
    """
    return {
        "standard_top_sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "standard_bottom_sizes": ["28", "30", "32", "34", "36", "38"],
        "description": "Standard sizes for shirts, t-shirts, hoodies, and waist sizes in inches for jeans/shorts.",
    }


# ==============================================================================
# FastMCP Cart Management Tools
# ==============================================================================

@mcp.tool()
async def add_to_cart(
    product_id: int,
    user_id: Optional[int] = None,
    quantity: int = 1,
    size: Optional[str] = None,
    discount_percentage: float = 0.0,
) -> Dict[str, Any]:
    """
    Adds an in-stock product to the customer's shopping cart.
    Supports attaching an agreed negotiated discount percentage.
    
    Parameters:
    - product_id (int, Required): The ID of the product to add.
    - user_id (int, Optional): Customer ID whose cart will be updated.
    - quantity (int, Optional, default=1): Number of units to add (must be at least 1).
    - size (str, Optional): Size of the apparel (e.g. 'M', 'L', 'XL' for tops; '30', '32', '34' for jeans).
    - discount_percentage (float, Optional, default=0.0): If price was negotiated with customer prior to adding, pass the approved discount percentage here.

    LLM Usage & Instructions:
    1. Call this tool when customer says 'add to cart', 'buy this', 'put this in my bag', or accepts a recommended product.
    2. NEGOTIATED ITEMS ONLY: If this specific product (product_id) was individually negotiated prior to adding, pass its approved 'discount_percentage'.
    3. UN-NEGOTIATED ITEMS (CRITICAL): If adding any other product that was NOT individually negotiated in this session, you MUST pass discount_percentage=0.0! NEVER transfer or copy another product's discount percentage to this item!
    4. If the user hasn't specified a size for clothing, ask them for their size, or pass a default size if agreed.
    4. MANDATORY AUTH CHECK: If user_id is NOT provided (or user is a guest/unauthenticated), do NOT call this tool. Instead, ask the user to log in or sign up first: [Log In or Sign Up](/login).
    5. Confirm addition by stating the product name, quantity, selected size, and any applied discount.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to add items to cart.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        payload = AddItemRequest(
            product_id=product_id,
            quantity=max(1, int(quantity)),
            size=size.strip().upper() if size else None,
            discount_percentage=float(discount_percentage or 0.0),
        )

        res = await cartController.add_item(
            user_id=user_id,
            payload=payload,
        )

        # Record user event: ADD_TO_CART for authenticated customer
        await record_user_event(
            user_id=user_id,
            product_id=product_id,
            event_type=EventType.ADD_TO_CART,
        )

        return {
            "success": True,
            "message": "Item added to cart successfully.",
            "item": res.get("item"),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add product {product_id} to cart: {str(e)}",
        }


@mcp.tool()
async def apply_cart_item_discount(
    product_id: int,
    discount_percentage: float,
    user_id: Optional[int] = None,
    size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Applies a negotiated discount percentage directly to an existing item in the customer's cart.
    
    Parameters:
    - product_id (int, Required): ID of the product in the cart.
    - discount_percentage (float, Required): Negotiated discount percent (between 0.0 and 100.0).
    - user_id (int, Optional): Customer ID.
    - size (str, Optional): Size of the item in the cart if applicable.
    """
    is_guest = user_id is None or user_id <= 0
    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to apply cart item discounts.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        payload = UpdateItemDiscountRequest(
            product_id=product_id,
            discount_percentage=float(discount_percentage),
            size=size.strip().upper() if size else None,
        )

        res = await cartController.update_item_discount(
            user_id=user_id,
            payload=payload,
        )

        return {
            "success": True,
            "message": res.get("message", "Cart item discount updated successfully."),
            "item": res.get("item"),
            "summary": res.get("summary"),
        }
    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update cart item discount for product {product_id}: {str(e)}",
        }


@mcp.tool()
async def get_cart_items(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieves all items currently present in the customer's shopping cart with their discounts and prices.
    
    Parameters:
    - user_id (int, Optional): Customer ID to look up cart items for.

    LLM Usage & Instructions:
    1. Call this tool when the user asks 'what's in my cart?', 'show my cart', or before beginning checkout/negotiation.
    2. If the cart is empty, gently inform the user and suggest browsing products.
    3. If user_id is NOT provided, remind the user to log in or register.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "items": [],
            "count": 0,
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        res = await cartController.get_items(user_id=user_id)

        return {
            "success": True,
            "items": res.get("items", []),
            "count": res.get("count", 0),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
            "items": [],
            "count": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve cart items: {str(e)}",
            "items": [],
            "count": 0,
        }


@mcp.tool()
async def update_cart_quantity(
    product_id: int,
    quantity: int,
    user_id: Optional[int] = None,
    size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates the quantity of an existing item in the customer's shopping cart.
    Setting quantity to 0 or less will remove the item from the cart.
    
    Parameters:
    - product_id (int, Required): The ID of the product in the cart.
    - quantity (int, Required): The new total quantity (0 to remove).
    - user_id (int, Optional): Customer ID.
    - size (str, Optional): Size of the item being updated.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to update cart items.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        payload = UpdateItemRequest(
            product_id=product_id,
            quantity=int(quantity),
            size=size.strip().upper() if size else None,
        )

        res = await cartController.update_item(
            user_id=user_id,
            payload=payload,
        )

        if int(quantity) <= 0:
            await record_user_event(
                user_id=user_id,
                product_id=product_id,
                event_type=EventType.REMOVE_FROM_CART,
            )

        return {
            "success": True,
            "message": res.get("message", "Cart item updated successfully."),
            "item": res.get("item"),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update quantity for product {product_id}: {str(e)}",
        }


@mcp.tool()
async def remove_from_cart(
    product_id: int,
    user_id: Optional[int] = None,
    size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Removes a specific product from the customer's shopping cart.
    
    Parameters:
    - product_id (int, Required): ID of the product to delete.
    - user_id (int, Optional): Customer ID.
    - size (str, Optional): Size of the product to remove.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to remove cart items.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        payload = DeleteItemRequest(
            product_id=product_id,
            size=size.strip().upper() if size else None,
        )

        res = await cartController.delete_item(
            user_id=user_id,
            payload=payload,
        )

        await record_user_event(
            user_id=user_id,
            product_id=product_id,
            event_type=EventType.REMOVE_FROM_CART,
        )

        return {
            "success": True,
            "message": res.get("message", "Item removed from cart successfully."),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to remove product {product_id} from cart: {str(e)}",
        }


@mcp.tool()
async def get_cart_summary(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieves the complete price breakdown of the customer's cart: subtotal,
    applied per-item discounts, items list, and total final payable price.
    
    Parameters:
    - user_id (int, Optional): Customer ID.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "subtotal": 0.0,
            "discount_amount": 0.0,
            "total_amount": 0.0,
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        res = await cartController.get_summary(user_id=user_id)

        return {
            "success": True,
            "subtotal": res.get("subtotal", 0.0),
            "discount_amount": res.get("discount_amount", 0.0),
            "total_amount": res.get("total_amount", 0.0),
            "effective_discount_percentage": res.get("effective_discount_percentage", 0.0),
            "items": res.get("items", []),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get cart summary: {str(e)}",
        }


@mcp.tool()
async def clear_cart(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Empties all items from the customer's shopping cart.
    
    Parameters:
    - user_id (int, Optional): Customer ID.
    """
    is_guest = user_id is None or user_id <= 0

    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to clear cart.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_CART,
        }

    try:
        try:
            cart_data = await cartController.get_items(user_id=user_id)
            for item in cart_data.get("items", []):
                pid = getattr(item, "product_id", None) or (item.get("product_id") if isinstance(item, dict) else None)
                if pid:
                    await record_user_event(
                        user_id=user_id,
                        product_id=pid,
                        event_type=EventType.REMOVE_FROM_CART,
                    )
        except Exception:
            pass

        res = await cartController.clear_cart(user_id=user_id)

        return {
            "success": True,
            "message": res.get("message", "Cart cleared successfully."),
        }

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clear cart: {str(e)}",
        }


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_cart_langchain_tools() -> List[StructuredTool]:
    """
    Returns all cart tools wrapped as native LangChain StructuredTool instances,
    ready to bind directly to LangGraph specialist agents with zero network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=add_to_cart,
            name="add_to_cart",
            description=add_to_cart.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=apply_cart_item_discount,
            name="apply_cart_item_discount",
            description=apply_cart_item_discount.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_cart_items,
            name="get_cart_items",
            description=get_cart_items.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=update_cart_quantity,
            name="update_cart_quantity",
            description=update_cart_quantity.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=remove_from_cart,
            name="remove_from_cart",
            description=remove_from_cart.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_cart_summary,
            name="get_cart_summary",
            description=get_cart_summary.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=clear_cart,
            name="clear_cart",
            description=clear_cart.__doc__,
        ),
    ]
