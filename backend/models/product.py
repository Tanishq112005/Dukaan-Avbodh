from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .order import Order


class ProductType(str, Enum):
    T_SHIRT = "t-shirt"
    SHORT = "short"
    SHIRT = "shirt"
    HOODIE = "hoodie"
    JEANS = "jeans"


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    cost_price: float = 0.0
    min_profit_margin_percent: float = 20.0   # naya — merchant chahta hai kam se kam itna % profit
    stock: int
    type: ProductType = ProductType.T_SHIRT
    brand: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    sizes: Optional[str] = None  # e.g., "S,M,L,XL"
    rating: float = 4.5
    discount: int = 0
    image_url: Optional[str] = None

    orders: List["Order"] = Relationship(back_populates="product")