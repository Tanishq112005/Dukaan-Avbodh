# schemas/product_schemas.py
from pydantic import BaseModel
from models.product import ProductType


class AddProductRequest(BaseModel):
    name: str
    price: float
    stock: int
    type: ProductType = ProductType.OTHER