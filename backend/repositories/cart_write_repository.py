from typing import Optional
from datetime import datetime
from sqlmodel import select, delete
from config.database import db_connection
from models.cart import Cart, CartItem
from repositories.cart_read_repository import CartReadRepository

class CartWriteRepository(CartReadRepository):
    async def add_item(self, user_id: int, product_id: int, quantity: int = 1, size: Optional[str] = None) -> CartItem:
        async with db_connection.get_session() as session:
            try:
                cart = await self.get_or_create_cart(user_id)
                existing = (await session.exec(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id, CartItem.size == size))).first()
                if existing:
                    existing.quantity += quantity
                    session.add(existing)
                    cart.updated_at = datetime.utcnow()
                    session.add(cart)
                    await session.commit()
                    await session.refresh(existing)
                    return existing
                item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, size=size)
                session.add(item)
                cart.updated_at = datetime.utcnow()
                session.add(cart)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e

    async def remove_item(self, user_id: int, product_id: int, size: Optional[str] = None) -> bool:
        async with db_connection.get_session() as session:
            try:
                cart = (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()
                if not cart: return False
                q = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
                if size: q = q.where(CartItem.size == size)
                item = (await session.exec(q)).first()
                if not item: return False
                await session.delete(item)
                cart.updated_at = datetime.utcnow()
                session.add(cart)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

    async def update_quantity(self, user_id: int, product_id: int, quantity: int, size: Optional[str] = None) -> Optional[CartItem]:
        if quantity <= 0: return await self.remove_item(user_id, product_id, size)
        async with db_connection.get_session() as session:
            try:
                cart = (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()
                if not cart: return None
                q = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
                if size: q = q.where(CartItem.size == size)
                item = (await session.exec(q)).first()
                if not item: return None
                item.quantity = quantity
                session.add(item)
                cart.updated_at = datetime.utcnow()
                session.add(cart)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e

    async def clear_cart(self, user_id: int) -> bool:
        async with db_connection.get_session() as session:
            try:
                cart = (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()
                if not cart: return False
                await session.exec(delete(CartItem).where(CartItem.cart_id == cart.id))
                cart.updated_at = datetime.utcnow()
                session.add(cart)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e
