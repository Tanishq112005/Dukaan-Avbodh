# controllers/product_controller.py
from fastapi import HTTPException
from schemas.product_schemas import AddProductRequest
from repositories import ProductRepository
from models import Product


class ProductController:
    def __init__(self):
        self.product_repo = ProductRepository()

    async def add_product(self, payload: AddProductRequest, merchant_id: int):
        product = Product(
            name=payload.name,
            price=payload.price,
            stock=payload.stock,
            type=payload.type
        )
        created = await self.product_repo.create(product)

        await self.audit_repo.log_action(
            action="product_added",
            reason=f"merchant {merchant_id} added product '{payload.name}'",
            result=f"product_id={created.id}"
        )
        return created

    async def get_catalog(self):
        return await self.product_repo.get_in_stock()

    async def get_by_type(self, product_type: str):
        from models.product import ProductType
        return await self.product_repo.get_by_type(ProductType(product_type))