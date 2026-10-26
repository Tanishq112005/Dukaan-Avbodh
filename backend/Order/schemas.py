from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class OrderRequest(BaseModel):
    amount: int  # in paise
    currency: str = "INR"
    receipt: str = "receipt_01"


class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = 1


class CheckoutRequest(BaseModel):
    items: Optional[List[CheckoutItem]] = None
    discount_percentage: Optional[float] = 0.0
    provider: Optional[str] = "razorpay"
    currency: Optional[str] = "INR"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None
