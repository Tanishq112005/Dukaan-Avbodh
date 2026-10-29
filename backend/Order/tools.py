import sys
import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from langchain_core.tools import StructuredTool

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

from Order.controller import orderController
from Payment.controller import paymentController

logger = logging.getLogger(__name__)

LOGIN_NUDGE_FOR_ORDERS = (
    "To view, place, or track your orders, please log in or sign up to Dukaan!"
)


# ==============================================================================
# FastMCP Order Resources
# ==============================================================================

@mcp.resource("order://policy")
async def get_order_policy_resource() -> Dict[str, Any]:
    """
    Returns store order, checkout, payment, and delivery policies for AI agents.
    """
    return {
        "checkout_policy": "Real-time stock reservation with concurrency locks.",
        "delivery_policy": "Standard Express Shipping: 3-5 Business Days across India.",
        "return_policy": "14-day hassle-free returns with doorstep pickup.",
        "cancellation_policy": "Orders can be cancelled before dispatch for a 100% full refund.",
    }


@mcp.resource("order://tracking-stages")
async def get_order_tracking_stages_resource() -> Dict[str, Any]:
    """
    Returns standard fulfillment tracking stages for Dukaan customer orders.
    """
    return {
        "stages": [
            {"step": 1, "name": "Placed", "description": "Order received and stock reserved."},
            {"step": 2, "name": "Quality Check", "description": "Garment quality and stitching inspection."},
            {"step": 3, "name": "Dispatched", "description": "Handed to courier partner with tracking ID."},
            {"step": 4, "name": "Delivered", "description": "Package safely handed to customer."},
        ]
    }


# ==============================================================================
# FastMCP Order Tools
# ==============================================================================

@mcp.tool()
async def checkout_order(
    user_id: Optional[int] = None,
    discount_percentage: float = 0.0,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    thread_id: str = "",
) -> Dict[str, Any]:
    """
    Places an order for all items currently in the customer's cart, reserves stock
    under multi-product concurrency locks, and generates a secure Razorpay payment link.

    Parameters:
    - user_id (int, Optional): Customer ID placing the order.
    - discount_percentage (float, Optional, default=0.0): Any agreed VIP/bargain discount percentage.
    - customer_name (str, Optional): Full name of the recipient for shipping.
    - customer_email (str, Optional): Recipient's email address for receipt and invoice.
    - thread_id (str, Optional): Current conversation session ID.

    LLM Usage & Instructions:
    1. Call this tool when the customer says 'I want to buy', 'checkout', 'place my order', or 'pay now'.
    2. The tool creates order rows, decrements inventory safely, and returns a 'payment_link'.
    3. In your response:
       - Congratulate them and display their order confirmation summary.
       - Always share the 'payment_link' formatted as a markdown link [Pay securely](payment_link)
         AND as a raw URL on its own line so they can complete payment with one click.
    """
    is_guest = user_id is None or user_id <= 0
    if is_guest:
        return {
            "success": False,
            "error": "A customer user_id is required to checkout.",
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_ORDERS,
        }

    try:
        from Cart.database import cart_repository
        if hasattr(cart_repository, "get_cart_items"):
            cart_items = await cart_repository.get_cart_items(user_id)
        else:
            cart_items = await cart_repository.get_items(user_id)
        if not cart_items:
            return {
                "success": False,
                "error": "Your shopping bag is empty. Please add items before placing an order.",
            }

        # Perform checkout with distributed inventory locking & Razorpay payment link generation
        checkout_res = await paymentController.checkout_with_concurrency_lock(
            user_id=user_id,
            items=None,  # reads directly from cart under lock
            discount_percentage=discount_percentage,
            provider="razorpay",
            customer_name=customer_name,
            customer_email=customer_email,
            generate_payment_link=True,
        )

        payment_link = checkout_res.get("payment_link_url")
        order_ids = checkout_res.get("order_ids", [])
        total_amount = checkout_res.get("total_amount", 0.0)

        # Update chat state patch if thread_id is available
        if thread_id:
            try:
                from Chat.database import chat_audit_repo
                await chat_audit_repo.update_state_patch(
                    user_id,
                    thread_id,
                    {
                        "order_placed": True,
                        "order_ids": order_ids,
                        "pending_payment_link": payment_link,
                        "pending_payment_link_id": checkout_res.get("payment_link_id"),
                        "payment_status": "pending_payment",
                        "ordered_items": cart_items,
                    },
                )
            except Exception as e:
                logger.debug("Failed updating chat audit state patch for checkout: %s", e)

        return {
            "success": True,
            "order_ids": order_ids,
            "total_amount": total_amount,
            "discount_applied": discount_percentage,
            "payment_link": payment_link or "Payment link unavailable",
            "payment_link_id": checkout_res.get("payment_link_id"),
            "razorpay_order_id": checkout_res.get("gateway_order_id"),
            "ordered_items": cart_items,
            "delivery_estimate": "3-5 Business Days",
            "message": f"Order #{order_ids[0] if order_ids else ''} reserved! Total amount is ₹{total_amount:.2f}.",
        }

    except Exception as e:
        logger.exception("checkout_order tool execution failed: %s", e)
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def get_my_orders(
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieves all past and active orders for the customer with product details,
    pricing, quantities, and current payment and delivery status.

    Parameters:
    - user_id (int, Optional): Customer ID whose order history is requested.

    LLM Usage & Instructions:
    1. Call this tool when the customer asks 'where are my orders?', 'show my orders',
       'order history', or 'what have I bought?'.
    2. Summarize recent orders clearly, including order ID, items, date, total, and status.
    """
    is_guest = user_id is None or user_id <= 0
    if is_guest:
        return {
            "success": False,
            "orders": [],
            "count": 0,
            "requires_login": True,
            "login_prompt": LOGIN_NUDGE_FOR_ORDERS,
        }

    try:
        res = await orderController.get_user_orders(user_id=user_id)
        orders = res.get("orders", [])

        return {
            "success": True,
            "orders": orders,
            "count": len(orders),
            "message": f"Found {len(orders)} order(s) for your account." if orders else "You have no orders yet.",
        }

    except Exception as e:
        logger.exception("get_my_orders tool execution failed: %s", e)
        return {
            "success": False,
            "orders": [],
            "count": 0,
            "error": str(e),
        }


@mcp.tool()
async def track_order(
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Tracks the live fulfillment, dispatch, and delivery status of a specific order
    or the customer's most recent order.

    Parameters:
    - order_id (int, Optional): Specific order ID to track. If omitted, tracks the latest order.
    - user_id (int, Optional): Customer ID.

    LLM Usage & Instructions:
    1. Call this tool when the customer asks 'track my order', 'where is order #123?',
       'has my order shipped?', or 'when will my order arrive?'.
    2. Inform the customer of their order ID, current stage (Placed, Quality Check, Dispatched, Delivered),
       and estimated delivery window.
    """
    try:
        res = await orderController.get_order_tracking(order_id=order_id, user_id=user_id)
        return res

    except Exception as e:
        logger.exception("track_order tool execution failed: %s", e)
        return {
            "success": False,
            "error": f"Failed to track order: {str(e)}",
        }


@mcp.tool()
async def cancel_order(
    order_id: int,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Cancels an order before it is dispatched, and safely restores reserved product stock
    using distributed concurrency locks.

    Parameters:
    - order_id (int, Required): The ID of the order to cancel.
    - user_id (int, Optional): Customer ID verifying order ownership.

    LLM Usage & Instructions:
    1. Call this tool when the customer explicitly asks to cancel an order (e.g. 'cancel order #45').
    2. Confirm cancellation and let them know that their item inventory has been restored.
    """
    try:
        # Verify ownership if user_id provided
        if user_id:
            order = await orderController.get_order_by_id(order_id, user_id=user_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order #{order_id} not found or does not belong to your account.",
                }

        res = await orderController.cancel_order(order_id=order_id)
        return res

    except HTTPException as http_err:
        return {
            "success": False,
            "error": http_err.detail,
        }
    except Exception as e:
        logger.exception("cancel_order tool execution failed: %s", e)
        return {
            "success": False,
            "error": f"Failed to cancel order #{order_id}: {str(e)}",
        }


@mcp.tool()
async def check_order_payment_status(
    user_id: Optional[int] = None,
    thread_id: str = "",
) -> Dict[str, Any]:
    """
    Checks whether the customer has completed payment on Razorpay for their pending order.

    Parameters:
    - user_id (int, Optional): Customer ID.
    - thread_id (str, Optional): Current conversation session ID.

    LLM Usage & Instructions:
    1. Call this tool when the customer says they finished paying, or on receiving a [SYSTEM EVENT: payment].
    2. If paid is true: Congratulate the customer warmly, confirm order completion, and advise them that their cart is now cleared.
    3. If paid is false: Politely inform them that payment is still pending and share the payment link again.
    """
    is_guest = user_id is None or user_id <= 0
    if is_guest:
        return {
            "success": False,
            "paid": False,
            "error": "A customer user_id is required to check payment status.",
        }

    try:
        status_res = await paymentController.get_user_payment_status(user_id=user_id)
        is_paid = status_res.paid

        if thread_id and is_paid:
            try:
                from Chat.database import chat_audit_repo
                await chat_audit_repo.update_state_patch(
                    user_id,
                    thread_id,
                    {"payment_status": "paid"},
                )
            except Exception:
                pass

        return {
            "success": True,
            "paid": is_paid,
            "status": status_res.status,
            "payment_link": status_res.payment_link,
            "razorpay_payment_id": status_res.gateway_payment_id,
            "message": (
                "Payment confirmed! Your order has been placed successfully and is being prepared for dispatch."
                if is_paid
                else "Payment is still pending. Please complete the transaction on the payment link."
            ),
        }

    except Exception as e:
        logger.exception("check_order_payment_status tool execution failed: %s", e)
        return {
            "success": False,
            "paid": False,
            "error": str(e),
        }


# ==============================================================================
# LangChain / LangGraph Adapter Helper
# ==============================================================================

def get_order_langchain_tools() -> List[StructuredTool]:
    """
    Returns all order management and tracking tools wrapped as native LangChain StructuredTools,
    ready to bind directly to the unified User Agent with zero network overhead.
    """
    return [
        StructuredTool.from_function(
            coroutine=checkout_order,
            name="checkout_order",
            description=checkout_order.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=get_my_orders,
            name="get_my_orders",
            description=get_my_orders.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=track_order,
            name="track_order",
            description=track_order.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=cancel_order,
            name="cancel_order",
            description=cancel_order.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=check_order_payment_status,
            name="check_order_payment_status",
            description=check_order_payment_status.__doc__,
        ),
    ]
