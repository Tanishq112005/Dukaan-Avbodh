from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional

from Payment.controller import paymentController
from Payment.schemas import (
    PaymentOrderCreateRequest,
    PaymentVerifyRequest,
    CheckoutWithLockRequest,
)
from Payment.routes import optional_user

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/create-order")
async def create_payment_order(
    payload: PaymentOrderCreateRequest,
    request: Request,
    user: Optional[dict] = Depends(optional_user),
):
    """Creates a payment order with Razorpay or the active provider."""
    user_id = user["user_id"] if user else None
    return await paymentController.create_payment_order(payload, user_id=user_id)


@router.post("/verify")
async def verify_payment(
    payload: PaymentVerifyRequest,
    request: Request,
    user: Optional[dict] = Depends(optional_user),
):
    """Verifies Razorpay HMAC signature and confirms orders in DB."""
    user_id = user["user_id"] if user else None
    return await paymentController.verify_payment(payload, user_id=user_id)


@router.post("/checkout")
async def checkout_with_lock(
    payload: CheckoutWithLockRequest,
    request: Request,
    user: Optional[dict] = Depends(optional_user),
):
    """
    Executes concurrency-locked checkout:
    Locks product stock, creates order in PENDING status, and generates payment order.
    """
    user_id = (user["user_id"] if user else None) or payload.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required for checkout")

    return await paymentController.checkout_with_concurrency_lock(
        user_id=user_id,
        items=payload.items,
        discount_percentage=payload.discount_percentage,
        provider=payload.provider,
        currency=payload.currency,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        generate_payment_link=False,
    )


@router.get("/status/{user_id}")
async def payment_status(user_id: int):
    """Checks user payment status."""
    return await paymentController.get_user_payment_status(user_id)


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay payment_link.paid / payment.captured / order.paid webhook."""
    return await paymentController.handle_webhook(request)
