# schemas/checkout_schemas.py
from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    product_id: int
    requested_discount: float = 0.0
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None