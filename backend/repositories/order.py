from typing import Optional, List
from sqlmodel import select
from sqlalchemy.orm import selectinload
from config.database import db_connection
from models import Order

class Order:
    def __init__(self , db_connection):
        self.db = db_connection

    async def create_orders_batch(self, orders: List[Order]) -> List[Order]:
        """Creates multiple orders in a single database transaction, preventing N+1 insert loops."""
        if not orders:
            return []
        async with self.db.get_session() as session:
            try:
                session.add_all(orders)
                await session.commit()
                for o in orders:
                    await session.refresh(o)
                return orders
            except Exception as e:
                await session.rollback()
                raise e

    async def get_with_relations(self, order_id: int) -> Optional[Order]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.product), selectinload(Order.user))
            )
            return result.first()

    async def get_by_user(self, user_id: int) -> List[Order]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Order).where(Order.user_id == user_id)
            )
            return result.all()

    async def update_status(self, order_id: int, status: str) -> Optional[Order]:
        async with self.db.get_session() as session:
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
            
            