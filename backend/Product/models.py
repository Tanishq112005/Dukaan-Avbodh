from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from Order.models import Order
    from recommedation.models import ProbabilityOfShowingItems, ProbabilityOfShowingItemsForParticularUser


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
    min_profit_margin_percent: float = 20.0
    stock: int
    type: ProductType 
    brand: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    sizes: Optional[str] = None
    rating: Optional[float] = None
    discount: int = 0
    image_url: Optional[str] = None

    orders: List["Order"] = Relationship(back_populates="product")
    probability_scores: list["ProbabilityOfShowingItems"] = Relationship(
        back_populates="product"
    )

    user_probability_scores: list[
        "ProbabilityOfShowingItemsForParticularUser"
    ] = Relationship(
        back_populates="product"
    )
