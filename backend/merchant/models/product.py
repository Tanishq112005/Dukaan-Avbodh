from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .order import Order   # sirf type-checking ke liye import, runtime pe nahi

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    stock: int

    orders: List["Order"] = Relationship(back_populates="product")