from enum import Enum
from typing import Any, List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from Order.models import Order
    from Recommedation.models import ProbabilityOfShowingItems, ProbabilityOfShowingItemsForParticularUser


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


def get_base_selling_price(product: Any) -> float:
    """
    Computes the standard public listing selling price of a product before discount.
    If merchant configured a discount (e.g. 15%), product.price in DB represents the
    discounted baseline (e.g. 1000), so the public selling price is round(1000 / (1 - 0.15)) = 1176.
    """
    if product is None:
        return 0.0
    if isinstance(product, dict):
        price = float(product.get("price", 0.0) or 0.0)
        disc = float(product.get("discount", 0) or 0)
    else:
        price = float(getattr(product, "price", 0.0) or 0.0)
        disc = float(getattr(product, "discount", 0) or 0)

    if 0 < disc < 100 and price > 0:
        return float(round(price / (1.0 - disc / 100.0)))
    return float(round(price, 2))
