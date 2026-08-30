# models/cart.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .product import Product


class Cart(SQLModel, table=True):
    """Har user ka ek hi active cart hota hai — yeh backend mein authoritative source hai,
    frontend ka cart sirf isi ka mirror hai."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    items: List["CartItem"] = Relationship(back_populates="cart")


class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="cart.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    size: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)

    cart: Optional["Cart"] = Relationship(back_populates="items")
