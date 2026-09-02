from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import razorpay
import os
import hmac
import hashlib
from services.payment_service import check_user_payment_status, mark_orders_paid

router = APIRouter(prefix="/payment", tags=["Payment"])

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TWV2ichCwzRcvo")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "9Ew8lMz1DUumk4hYVPBbf4dd")

try:
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    rzp_client = None


class OrderRequest(BaseModel):
    amount: int  # in paise
    currency: str = "INR"
    receipt: str = "receipt_01"

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
async def create_payment_order(payload: OrderRequest):
    if not rzp_client:
        raise HTTPException(status_code=500, detail="Razorpay client not configured")
    
    if payload.amount < 100:
        raise HTTPException(status_code=400, detail="Amount must be at least 100 paise (1 INR)")
    
    try:
        order = rzp_client.order.create({
            "amount": payload.amount,
            "currency": payload.currency,
            "receipt": payload.receipt
        })
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_payment(payload: VerifyRequest):
    try:
        # Standard Razorpay HMAC Verification
        msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature == payload.razorpay_signature:
            await mark_orders_paid(
                razorpay_order_id=payload.razorpay_order_id,
                razorpay_payment_id=payload.razorpay_payment_id,
            )
            return {"success": True, "message": "Payment verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Signature mismatch")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{user_id}")
async def payment_status(user_id: int):
    return await check_user_payment_status(user_id)


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay payment_link.paid / payment.captured — marks the order paid so the agent can see it."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = body.get("event", "")
    payload = body.get("payload") or {}
    paid = event in ("payment_link.paid", "payment.captured", "order.paid")

    payment_entity = (payload.get("payment") or {}).get("entity") or {}
    link_entity = (payload.get("payment_link") or {}).get("entity") or {}
    order_entity = (payload.get("order") or {}).get("entity") or {}

    if not paid:
        status = link_entity.get("status") or payment_entity.get("status")
        paid = status == "paid"

    if paid:
        notes = link_entity.get("notes") or order_entity.get("notes") or {}
        user_id = None
        try:
            user_id = int(notes.get("user_id")) if notes.get("user_id") else None
        except (TypeError, ValueError):
            user_id = None
        updated = await mark_orders_paid(
            user_id=user_id,
            payment_link_id=link_entity.get("id"),
            razorpay_order_id=order_entity.get("id") or (link_entity.get("notes") or {}).get("order_id"),
            razorpay_payment_id=payment_entity.get("id"),
        )
        return {"success": True, "updated": updated}

    return {"success": True, "ignored": True}
