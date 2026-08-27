# schemas/checkout_schemas.py
from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    product_id: int
    requested_discount: float = 0.0