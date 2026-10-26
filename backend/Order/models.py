from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum


if TYPE_CHECKING:
    from Product.models import Product
    from User.models import User


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    user_id: int = Field(foreign_key="user.id")
    quantity: int = Field(default=1)
    gateway_order_id: Optional[str] = Field(default=None)
    gateway_payment_id: Optional[str] = Field(default=None)
    gateway_link_id: Optional[str] = Field(default=None)
    payment_link_url: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default="razorpay")
    payment_status: str = Field(default=PaymentStatus.PENDING)
    payment_attempts: int = Field(default=0)
    total_amount: float = Field(default=0.0)
    discount_applied: float = Field(default=0.0)
    payment_method: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

    product: Optional["Product"] = Relationship(back_populates="orders")
    user: Optional["User"] = Relationship(back_populates="orders")

    # Backward-compatible property aliases
    @property
    def razorpay_order_id(self) -> Optional[str]:
        return self.gateway_order_id

    @razorpay_order_id.setter
    def razorpay_order_id(self, value: Optional[str]):
        self.gateway_order_id = value

    @property
    def razorpay_payment_id(self) -> Optional[str]:
        return self.gateway_payment_id

    @razorpay_payment_id.setter
    def razorpay_payment_id(self, value: Optional[str]):
        self.gateway_payment_id = value

    @property
    def razorpay_payment_link_id(self) -> Optional[str]:
        return self.gateway_link_id

    @razorpay_payment_link_id.setter
    def razorpay_payment_link_id(self, value: Optional[str]):
        self.gateway_link_id = value

    @property
    def status(self) -> str:
        return self.payment_status

    @status.setter
    def status(self, value: str):
        self.payment_status = value
