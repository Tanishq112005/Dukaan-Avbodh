# models/order.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
if TYPE_CHECKING:
    from .product import Product
    from .user import User


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    
class DeilveredStatus(str , Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    RETURNED = "returned"
    
class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    user_id: int = Field(foreign_key="user.id")          
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    provider: Optional[str] = None
    payment_status: str = PaymentStatus.PENDING
    total_amount: float = 0.0
    payment_method: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    delivered_status: str = DeilveredStatus.PENDING
    
    
    product: Optional["Product"] = Relationship(back_populates="orders")
    user: Optional["User"] = Relationship(back_populates="orders")