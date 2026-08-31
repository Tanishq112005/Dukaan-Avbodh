from typing import Optional, List
from sqlmodel import select
from sqlalchemy.orm import selectinload
from config.database import db_connection
from models import Order
from .base_repository import BaseRepository

class OrderRepository(BaseRepository[Order]):
    def __init__(self):
        super().__init__(Order)

    async def get_with_relations(self, order_id: int) -> Optional[Order]:
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.product), selectinload(Order.user))
            )
            return result.first()

    async def get_by_user(self, user_id: int) -> List[Order]:
        async with db_connection.get_session() as session:
            result = await session.exec(
                select(Order).where(Order.user_id == user_id)
            )
            return result.all()

    async def update_status(self, order_id: int, status: str) -> Optional[Order]:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(
                    select(Order).where(Order.id == order_id)
                )
                order = result.first()
                if order:
                    order.status = status
                    session.add(order)
                    await session.commit()
                    await session.refresh(order)
                return order
            except Exception as e:
                await session.rollback()
                raise e