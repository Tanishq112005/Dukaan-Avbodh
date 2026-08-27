# repositories/product_repository.py
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
            finally:
                await session.close()

    async def get_in_stock(self) -> List[Product]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(Product).where(Product.stock > 0)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()

    async def get_by_type(self, product_type: ProductType) -> List[Product]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(Product).where(Product.type == product_type)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()