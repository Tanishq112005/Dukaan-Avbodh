# repositories/cart_repository.py
from typing import Optional, List
from sqlmodel import select
from config.database import db_connection
from models.cart import Cart, CartItem
from models.product import Product


class CartRepository:
    """
    Backend-authoritative cart. Har user ka ek hi Cart row hota hai.
    Frontend ka cart state sirf UI ke liye mirror hai — asli source yeh hai,
    taaki chat agent aur MCP (external agent) dono isi cart ko padh/likh saken.
    """

    async def get_or_create_cart(self, user_id: int) -> Cart:
        async with db_connection.get_session() as session:
            try:
                result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = result.first()
                if cart:
                    return cart
                cart = Cart(user_id=user_id)
                session.add(cart)
                await session.commit()
                await session.refresh(cart)
                return cart
            finally:
                await session.close()

    async def get_cart_items(self, user_id: int) -> List[dict]:
        """Cart items ko product details ke saath enrich karke return karta hai."""
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return []

                items_result = await session.exec(select(CartItem).where(CartItem.cart_id == cart.id))
                items = items_result.all()

                enriched: List[dict] = []
                for item in items:
                    p_result = await session.exec(select(Product).where(Product.id == item.product_id))
                    product = p_result.first()
                    if not product:
                        continue
                    enriched.append({
                        "cart_item_id": item.id,
                        "id": product.id,
                        "product_id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "quantity": item.quantity,
                        "size": item.size,
                        "type": product.type.value,
                        "gender": product.gender,
                        "image_url": product.image_url,
                    })
                return enriched
            finally:
                await session.close()

    async def add_item(self, user_id: int, product_id: int, quantity: int = 1, size: Optional[str] = None) -> CartItem:
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    cart = Cart(user_id=user_id)
                    session.add(cart)
                    await session.commit()
                    await session.refresh(cart)

                # Agar same product+size already cart mein hai, quantity badha do (duplicate row mat banao)
                existing_result = await session.exec(
                    select(CartItem).where(
                        CartItem.cart_id == cart.id,
                        CartItem.product_id == product_id,
                        CartItem.size == size,
                    )
                )
                existing = existing_result.first()
                if existing:
                    existing.quantity += quantity
                    session.add(existing)
                    await session.commit()
                    await session.refresh(existing)
                    return existing

                item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, size=size)
                session.add(item)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def remove_item(self, user_id: int, product_id: int, size: Optional[str] = None) -> bool:
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return False

                query = select(CartItem).where(
                    CartItem.cart_id == cart.id, CartItem.product_id == product_id
                )
                if size is not None:
                    query = query.where(CartItem.size == size)

                result = await session.exec(query)
                item = result.first()
                if not item:
                    return False

                await session.delete(item)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def update_quantity(
        self, user_id: int, product_id: int, quantity: int, size: Optional[str] = None
    ) -> Optional[CartItem]:
        """quantity <= 0 bhejne par item cart se remove ho jaata hai."""
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return None

                query = select(CartItem).where(
                    CartItem.cart_id == cart.id, CartItem.product_id == product_id
                )
                if size is not None:
                    query = query.where(CartItem.size == size)

                result = await session.exec(query)
                item = result.first()
                if not item:
                    return None

                if quantity <= 0:
                    await session.delete(item)
                    await session.commit()
                    return None

                item.quantity = quantity
                session.add(item)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def clear_cart(self, user_id: int) -> bool:
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return False

                items_result = await session.exec(select(CartItem).where(CartItem.cart_id == cart.id))
                items = items_result.all()
                for item in items:
                    await session.delete(item)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()


cart_repository = CartRepository()
