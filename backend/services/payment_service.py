"""
Legacy payment service adapter.
Delegates to the modern, extensible Payment and Order architecture.
"""
from typing import Optional, Dict, Any
from Payment.controller import paymentController
from Order.database import order_repository
from Payment.factory import payment_gateway_factory

# Backward-compatible client access
rzp_gateway = payment_gateway_factory.get_gateway("razorpay")
rzp_client = getattr(rzp_gateway, "client", None)


async def mark_orders_paid(
    *,
    user_id: Optional[int] = None,
    payment_link_id: Optional[str] = None,
    razorpay_order_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
) -> int:
    """Mark matching pending orders as paid. Returns number of rows updated."""
    updated_orders = await order_repository.confirm_order_payment(
        gateway_order_id=razorpay_order_id,
        gateway_payment_id=razorpay_payment_id,
        user_id=user_id,
    )
    return len(updated_orders)


async def check_user_payment_status(user_id: int) -> Dict[str, Any]:
    """Polls payment status for user."""
    res = await paymentController.get_user_payment_status(user_id)
    return {
        "success": res.success,
        "paid": res.paid,
        "status": res.status,
        "payment_link": res.payment_link,
        "payment_link_id": res.payment_link_id,
        "razorpay_payment_id": res.gateway_payment_id,
        "message": res.message,
    }
