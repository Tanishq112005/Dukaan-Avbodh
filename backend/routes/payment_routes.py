from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import razorpay
import os
import hmac
import hashlib

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
            return {"success": True, "message": "Payment verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Signature mismatch")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
