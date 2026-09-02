from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from models import Product
from models.product import ProductType
from .base_repository import BaseRepository

class ProductRepository(BaseRepository[Product]):
    def __init__(self):
        super().__init__(Product)

    async def update_stock(self, product_id: int, new_stock: int) -> Optional[Product]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(Product).where(Product.id == product_id)
                )
                product = result.first()
                if product:
                    product.stock = new_stock
                    session.add(product)
                    await session.commit()
                    await session.refresh(product)
                return product
            except Exception as e:
                await session.rollback()
                raise e

    async def get_in_stock(self) -> List[Product]:
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Product).where(Product.stock > 0)
            )
            return result.all()

    async def get_by_type(self, product_type: ProductType) -> List[Product]:
        """Fetches products of a specific type that are currently in stock."""
        async with db_connection.get_session() as session:
            result = await session.exec(
                # Added Product.stock > 0 to ensure out-of-stock items are filtered out
                select(Product).where(
                    Product.type == product_type, 
                    Product.stock > 0
                )
            )
            return result.all()

    async def get_by_ids(self, product_ids: List[int]) -> List[Product]:
        if not product_ids:
            return []
        async with db_connection.get_session() as session:
            result = await session.exec(select(Product).where(Product.id.in_(product_ids)))
            return result.all()

    async def get_in_stock_by_types(self, product_types: List[ProductType]) -> List[Product]:
        if not product_types:
            return []
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Product).where(
                    Product.type.in_(product_types),
                    Product.stock > 0,
                )
            )
            return result.all()