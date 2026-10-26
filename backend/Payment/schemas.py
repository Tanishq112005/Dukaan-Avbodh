from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class PaymentOrderCreateRequest(BaseModel):
    amount: int = Field(..., description="Amount in paise (e.g. 100 paise = 1 INR)", ge=100)
    currency: str = Field(default="INR")
    receipt: Optional[str] = Field(default=None)
    notes: Optional[Dict[str, Any]] = Field(default=None)
    provider: Optional[str] = Field(default="razorpay")
    order_ids: Optional[List[int]] = Field(default=None)


class PaymentOrderResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    receipt: Optional[str] = None
    provider: str
    client_key_id: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    provider: Optional[str] = Field(default="razorpay")
    order_ids: Optional[List[int]] = Field(default=None)


class PaymentVerifyResponse(BaseModel):
    success: bool
    message: str
    order_ids: Optional[List[int]] = None


class PaymentStatusResponse(BaseModel):
    success: bool
    paid: bool
    status: str
    message: str
    payment_link: Optional[str] = None
    payment_link_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None


class CheckoutWithLockRequest(BaseModel):
    user_id: Optional[int] = None
    items: Optional[List[Dict[str, Any]]] = None
    discount_percentage: float = 0.0
    provider: str = "razorpay"
    currency: str = "INR"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
