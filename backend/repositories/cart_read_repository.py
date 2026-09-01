from typing import List, Optional
from datetime import datetime
from sqlmodel import select
from config.database import db_connection
from models.cart import Cart, CartItem
from models.product import Product

class CartReadRepository:
    async def get_or_create_cart(self, user_id: int) -> Cart:
        async with db_connection.get_session() as session:
            try:
                cart = (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()
                if cart: return cart
                cart = Cart(user_id=user_id)
                session.add(cart)
                await session.commit()
                await session.refresh(cart)
                return cart
            except Exception as e:
                await session.rollback()
                raise e

    async def get_cart_items(self, user_id: int) -> List[dict]:
        async with db_connection.get_session() as session:
            cart = (await session.exec(select(Cart).where(Cart.user_id == user_id))).first()
            if not cart: return []
            query = select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.cart_id == cart.id)
            results = await session.exec(query)
            return [{
                "cart_item_id": i.id, "id": p.id, "product_id": p.id, "name": p.name,
                "price": p.price, "quantity": i.quantity, "size": i.size,
                "type": p.type.value if hasattr(p.type, "value") else p.type,
                "gender": p.gender, "image_url": p.image_url,
            } for i, p in results]
