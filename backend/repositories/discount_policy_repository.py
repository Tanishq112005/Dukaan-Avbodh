from typing import Optional
from sqlmodel import select
from config.database import db_connection
from Merchant.models import DiscountPolicy

class DiscountPolicyRepository:
    def __init__(self):
        pass

    async def get_for_product(self, product_id: int) -> Optional[DiscountPolicy]:
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(DiscountPolicy).where(DiscountPolicy.product_id == product_id)
            )
            return result.first()