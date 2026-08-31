# repositories/cart_repository.py
from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import select, delete
from config.database import db_connection

# Ensure this matches your file structure. 
# It imports the CLASSES Cart and CartItem from the file models/cart.py
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
            except Exception as e:
                await session.rollback()
                raise e

    async def get_cart_items(self, user_id: int) -> List[dict]:
        """
        Cart items ko product details ke saath enrich karke return karta hai.
        JOIN query use karta hai taaki N+1 problem na ho.
        """
        async with db_connection.get_session() as session:
            cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
            cart = cart_result.first()
            if not cart:
                return []

            # Single SQL JOIN query fetching both CartItem and Product simultaneously
            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )
            results = await session.exec(query)

            enriched: List[dict] = []
            for item, product in results:
                enriched.append({
                    "cart_item_id": item.id,
                    "id": product.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": item.quantity,
                    "size": item.size,
                    "type": product.type.value if hasattr(product.type, "value") else product.type,
                    "gender": product.gender,
                    "image_url": product.image_url,
                })
            return enriched

    async def add_item(
        self, user_id: int, product_id: int, quantity: int = 1, size: Optional[str] = None
    ) -> CartItem:
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    cart = Cart(user_id=user_id)
                    session.add(cart)
                    await session.commit()
                    await session.refresh(cart)

                # Check if item with same product_id and size exists
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
                    cart.updated_at = datetime.now(timezone.utc)
                    session.add(cart)
                    await session.commit()
                    await session.refresh(existing)
                    return existing

                item = CartItem(
                    cart_id=cart.id,
                    product_id=product_id,
                    quantity=quantity,
                    size=size,
                )
                session.add(item)
                cart.updated_at = datetime.now(timezone.utc)
                session.add(cart)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e

    async def remove_item(
        self, user_id: int, product_id: int, size: Optional[str] = None
    ) -> bool:
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return False

                query = select(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == product_id,
                )
                if size is not None:
                    query = query.where(CartItem.size == size)

                result = await session.exec(query)
                item = result.first()
                if not item:
                    return False

                await session.delete(item)
                cart.updated_at = datetime.now(timezone.utc)
                session.add(cart)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e

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
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == product_id,
                )
                if size is not None:
                    query = query.where(CartItem.size == size)

                result = await session.exec(query)
                item = result.first()
                if not item:
                    return None

                if quantity <= 0:
                    await session.delete(item)
                    cart.updated_at = datetime.now(timezone.utc)
                    session.add(cart)
                    await session.commit()
                    return None

                item.quantity = quantity
                session.add(item)
                cart.updated_at = datetime.now(timezone.utc)
                session.add(cart)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as e:
                await session.rollback()
                raise e

    async def clear_cart(self, user_id: int) -> bool:
        """Single bulk DELETE query ke through poora cart empty karta hai."""
        async with db_connection.get_session() as session:
            try:
                cart_result = await session.exec(select(Cart).where(Cart.user_id == user_id))
                cart = cart_result.first()
                if not cart:
                    return False

                # Bulk delete using SQL statement instead of item-by-item loop
                await session.exec(delete(CartItem).where(CartItem.cart_id == cart.id))
                cart.updated_at = datetime.now(timezone.utc)
                session.add(cart)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e


cart_repository = CartRepository()