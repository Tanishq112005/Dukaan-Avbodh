from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .product import Product


class ProbabilityOfShowingItems(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    product_id: int = Field(
        foreign_key="product.id",
        index=True
    )

    score: float = Field(default=0.0)

    product: Optional["Product"] = Relationship(
        back_populates="probability_scores"
    )


class ProbabilityOfShowingItemsForParticularUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="user.id",
        index=True
    )

    product_id: int = Field(
        foreign_key="product.id",
        index=True
    )

    score: float = Field(default=0.0)

    product: Optional["Product"] = Relationship(
        back_populates="user_probability_scores"
    )
