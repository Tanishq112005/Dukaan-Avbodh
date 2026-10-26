from pydantic import BaseModel, Field
from typing import Optional, List


class AddItemRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product to add")
    quantity: int = Field(default=1, gt=0, description="Quantity of the product, must be greater than 0")
    size: Optional[str] = Field(default=None, description="Optional size specification (e.g. S, M, L, XL)")
    discount_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Optional negotiated discount percentage for this product")
    discounted_price: Optional[float] = Field(default=None, ge=0.0, description="Optional negotiated unit price for this product")


class UpdateItemRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product to update")
    quantity: int = Field(..., description="New quantity of the product (<= 0 removes the item)")
    size: Optional[str] = Field(default=None, description="Optional size specification")


class UpdateItemDiscountRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product in the cart")
    discount_percentage: float = Field(..., ge=0.0, le=100.0, description="Negotiated discount percentage for this item")
    discounted_price: Optional[float] = Field(default=None, ge=0.0, description="Optional discounted price per unit")
    size: Optional[str] = Field(default=None, description="Optional size specification")


class DeleteItemRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product to delete")
    size: Optional[str] = Field(default=None, description="Optional size specification")


class ApplyDiscountRequest(BaseModel):
    discount_percentage: float = Field(..., ge=0.0, le=100.0, description="Discount percentage between 0 and 100")
