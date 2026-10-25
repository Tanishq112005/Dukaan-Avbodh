from typing import Optional
from pydantic import BaseModel, Field

from Product.models import ProductType


class ProductUpdate(BaseModel):
    product_id: int = Field(
        description="ID of the product that needs to be updated"
    )

    name: Optional[str] = Field(
        default=None,
        description="New product name"
    )

    price: Optional[float] = Field(
        default=None,
        gt=0,
        description="New selling price of the product"
    )

    cost_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="New cost price of the product"
    )

    min_profit_margin_percent: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum required profit margin percentage"
    )

    stock: Optional[int] = Field(
        default=None,
        ge=0,
        description="New available stock quantity"
    )

    type: Optional[ProductType] = Field(
        default=None,
        description="Product category: t-shirt, short, shirt, hoodie, or jeans"
    )

    brand: Optional[str] = Field(
        default=None,
        description="New product brand"
    )

    gender: Optional[str] = Field(
        default=None,
        description="Target gender for the product"
    )

    description: Optional[str] = Field(
        default=None,
        description="New product description"
    )

    sizes: Optional[str] = Field(
        default=None,
        description="Available sizes for the product"
    )

    rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5,
        description="Product rating between 0 and 5"
    )

    discount: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Product discount percentage between 0 and 100"
    )

    image_url: Optional[str] = Field(
        default=None,
        description="URL of the product image"
    )


class AddProductRequest(BaseModel):
    name: str
    price: float
    stock: int
    type: ProductType = ProductType.T_SHIRT
    brand: str | None = None
    gender: str | None = None
    description: str | None = None
    sizes: str | None = None
    rating: float = 4.5
    discount: int = 0
    image_url: str | None = None
