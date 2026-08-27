# repositories/product_repository.py
from typing import Optional
from sqlmodel import select
from db import async_session
from models import Product
from .base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self):
        super().__init__(Product)

    async def update_stock(self, product_id: int, new_stock: int) -> Optional[Product]:
        async with async_session() as session:
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

    async def get_in_stock(self) -> list[Product]:
        async with async_session() as session:
            try:
                result = await session.exec(
                    select(Product).where(Product.stock > 0)
                )
                return result.all()
            except Exception as e:
                raise e
            finally:
                await session.close()