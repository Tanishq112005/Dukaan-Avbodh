import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import StructuredTool

from Payment.controller import paymentController

logger = logging.getLogger(__name__)


async def create_payment_order(
    user_id: int,
    discount: float = 0.0,
    thread_id: str = "",
) -> Dict[str, Any]:
    """
    Creates an order for items in the user's cart with concurrency locking and generates a Razorpay payment link.

    LLM Usage:
    - Call this when the user is ready to buy or checkout their items.
    - When you receive the response, ALWAYS share the 'payment_link' formatted as a markdown link:
      [Pay securely](payment_link) and on its own line so the user can easily click and pay!
    """
    try:
        from Cart.database import cart_repository
        if hasattr(cart_repository, "get_cart_items"):
            cart_items = await cart_repository.get_cart_items(user_id)
        else:
            cart_items = await cart_repository.get_items(user_id)
        if not cart_items:
            return {
                "success": False,
                "error": "Your cart is currently empty. Please add items to your cart before proceeding to checkout.",
            }

        checkout_res = await paymentController.checkout_with_concurrency_lock(
            user_id=user_id,
            items=None,  # reads directly from cart under lock
            discount_percentage=discount,
            provider="razorpay",
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
                    },
                )
            except Exception as e:
                logger.debug("Failed updating chat audit state patch: %s", e)

        return {
            "success": True,
            "order_ids": order_ids,
            "total_amount": total_amount,
            "payment_link": payment_link or "Payment link unavailable",
            "payment_link_id": checkout_res.get("payment_link_id"),
            "razorpay_order_id": checkout_res.get("gateway_order_id"),
            "message": f"Order #{order_ids[0] if order_ids else ''} reserved! Total is ₹{total_amount:.2f}.",
        }

    except Exception as e:
        logger.exception("create_payment_order tool execution failed: %s", e)
        return {
            "success": False,
            "error": str(e),
        }


async def check_payment_status(
    user_id: int,
    thread_id: str = "",
) -> Dict[str, Any]:
    """
    Checks whether the shopper has successfully paid on Razorpay for their pending order.

    LLM Usage:
    - Call this when the customer says they completed their payment, or on [SYSTEM EVENT: payment].
    - If paid is true: Congratulate the customer warmly, confirm their order has been placed, and let them know their cart is now cleared.
    - If paid is false: Politely inform them that payment is still pending and invite them to finish paying via the link.
    """
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
                "Payment confirmed! The order has been finalized and will be shipped soon."
                if is_paid
                else "Payment is still pending. Please complete the transaction on the payment link."
            ),
        }
    except Exception as e:
        logger.exception("check_payment_status tool execution failed: %s", e)
        return {
            "success": False,
            "paid": False,
            "error": str(e),
        }


def get_payment_langchain_tools() -> List[StructuredTool]:
    """
    Returns payment tools wrapped as native LangChain StructuredTools for the User Agent.
    """
    return [
        StructuredTool.from_function(
            coroutine=create_payment_order,
            name="create_payment_order",
            description=create_payment_order.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=check_payment_status,
            name="check_payment_status",
            description=check_payment_status.__doc__,
        ),
    ]
