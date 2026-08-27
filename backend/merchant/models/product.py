from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .order import Order


class ProductType(str, Enum):
    CLOTHING = "clothing"
    ELECTRONICS = "electronics"
    FOOTWEAR = "footwear"
    ACCESSORIES = "accessories"
    GROCERY = "grocery"
    OTHER = "other"


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    stock: int
    type: ProductType = ProductType.OTHER

    orders: List["Order"] = Relationship(back_populates="product")