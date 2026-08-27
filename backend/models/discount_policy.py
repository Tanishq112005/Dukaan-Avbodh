from sqlmodel import SQLModel, Field
from typing import Optional

class DiscountPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    max_discount_percent: float
    min_qty_for_discount: int = 1
    
    