# models/order.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .product import Product
    from .user import User

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")          # naya field — pehle "buyer_agent: str" tha
    discount_applied: float = 0.0
    status: str = "pending"
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_payment_link_id: Optional[str] = None
    payment_link_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    product: Optional["Product"] = Relationship(back_populates="orders")
    user: Optional["User"] = Relationship(back_populates="orders")