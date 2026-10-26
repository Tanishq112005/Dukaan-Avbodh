from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Optional

from Payment.controller import paymentController
from Payment.schemas import (
    PaymentOrderCreateRequest,
    PaymentVerifyRequest,
    CheckoutWithLockRequest,
)
from middleware.auth_middleware import auth_middleware

router = APIRouter(prefix="/payment", tags=["Payment"])


async def optional_user(request: Request) -> Optional[dict]:
    """Extracts authenticated user if token is present, otherwise returns None."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            return await auth_middleware(request)
        except Exception:
            return None
    return None


@router.post("/create-order")
async def create_payment_order(
    payload: PaymentOrderCreateRequest,
    request: Request,
    user: Optional[dict] = Depends(optional_user),
):
    """
    Creates a payment order with Razorpay or the configured payment gateway.
    """
    user_id = user["user_id"] if user else None
    return await paymentController.create_payment_order(payload, user_id=user_id)


@router.post("/verify")
async def verify_payment(
    payload: PaymentVerifyRequest,
    request: Request,
    user: Optional[dict] = Depends(optional_user),
):
    """
    Verifies the payment gateway signature and confirms the order.
    """
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required for checkout",
        )

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
    """
    Polls real-time payment status for a user's recent orders.
    """
    return await paymentController.get_user_payment_status(user_id)


@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Receives and cryptographically verifies webhooks from Razorpay
    to finalize paid orders in real-time.
    """
    return await paymentController.handle_webhook(request)
