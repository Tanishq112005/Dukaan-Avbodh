from typing import Optional
from sqlmodel import select
from db import async_session
from models import DiscountPolicy
from .base_repository import BaseRepository


class DiscountPolicyRepository(BaseRepository[DiscountPolicy]):
    def __init__(self):
        super().__init__(DiscountPolicy)

    async def get_for_product(self, product_id: int) -> Optional[DiscountPolicy]:
        async with async_session() as session:
            try:
                result = await session.exec(
                    select(DiscountPolicy).where(DiscountPolicy.product_id == product_id)
                )
                return result.first()
            except Exception as e:
                raise e
            finally:
                await session.close()