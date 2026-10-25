from pydantic import BaseModel, Field
from typing import List, Optional


class NegotiationItemDTO(BaseModel):
    name: Optional[str] = None
    product_id: Optional[int] = None
    cost_price: float = Field(default=0.0, ge=0.0, description="Cost price per unit")
    price: float = Field(default=0.0, ge=0.0, description="Selling price per unit")
    min_profit_margin_percent: float = Field(
        default=0.0, ge=0.0, description="Minimum profit margin percentage required"
    )
    quantity: int = Field(default=1, ge=1, description="Quantity of the item")


class MaxDiscountRequest(BaseModel):
    user_id: Optional[int] = Field(
        default=None, description="Optional user ID to fetch items from user cart in DB"
    )
    items: Optional[List[NegotiationItemDTO]] = Field(
        default=None, description="List of items provided directly in JSON"
    )


class MaxDiscountResponse(BaseModel):
    total_selling_price: float
    total_cost_price: float
    total_minimum_selling_price: float
    max_discount_amount: float
    max_discount_percentage: float
    is_loss_leader: bool


class NextDiscountRequest(BaseModel):
    user_id: Optional[int] = Field(
        default=None, description="Optional user ID to fetch items from user cart in DB"
    )
    requested_discount_percent: float = Field(
        ..., ge=0.0, le=100.0, description="The discount percent asked by the user"
    )
    current_discount_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="The discount percent currently granted"
    )
    items: Optional[List[NegotiationItemDTO]] = Field(
        default=None, description="List of items provided directly in JSON"
    )
    apply_to_cart: bool = Field(
        default=False, description="If True and user_id is provided, automatically updates cart in DB"
    )


class NextDiscountResponse(BaseModel):
    accepted: bool
    current_discount_percent: float
    requested_discount_percent: float
    next_discount_percent: float
    counter_offer_price: float
    total_original_price: float
    absolute_max_discount_percent: float
    customer_tier: str = "loyal"
    reason: str
