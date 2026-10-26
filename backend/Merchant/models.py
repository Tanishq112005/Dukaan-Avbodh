from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class MerchantDiscountPolicy(SQLModel, table=True):
    """
    Storewide pricing and margin negotiation floor policy for Dukaan merchants.
    Defines the boundaries within which AI buyer agents are permitted to negotiate discounts.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: Optional[int] = Field(default=1, index=True)
    max_discount_percentage: float = Field(default=25.0)
    min_margin_percentage: float = Field(default=15.0)
    auto_accept_threshold: float = Field(default=10.0)
    updated_at: datetime = Field(default_factory=datetime.now)


class DiscountPolicy(SQLModel, table=True):
    """
    Per-product discount policy boundaries.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    base_discount_percent: float = 0.0
    max_discount_percent: float = 20.0
    agent_step_percent: float = 2.0
    min_loyalty_score: float = 0.0
    min_qty_for_discount: int = 1
