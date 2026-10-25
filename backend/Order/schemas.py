from pydantic import BaseModel
from typing import Optional


class OrderRequest(BaseModel):
    amount: int  # in paise
    currency: str = "INR"
    receipt: str = "receipt_01"


class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
