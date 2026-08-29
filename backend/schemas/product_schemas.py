# schemas/product_schemas.py
from pydantic import BaseModel
from models.product import ProductType


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