from typing import Optional
from datetime import datetime
from config.database import db_connection
from sqlmodel import select, delete

from Cart.models import Cart as CartModel, CartItem
from Product.models import Product


class Cart:

    def __init__(self, db_connection=None):
        from config.database import db_connection as default_db
        self.db = db_connection or default_db

    # Get or create the user's cart
    async def _get_cart(self, user_id: int, session) -> CartModel:
        cart = (
            await session.exec(
                select(CartModel).where(
                    CartModel.user_id == user_id
                )
            )
        ).first()

        if not cart:
            cart = CartModel(
                user_id=user_id,
                discount_percentage=0.0
            )
            session.add(cart)
            await session.flush()
            await session.refresh(cart)

        return cart

    async def get_cart(self, user_id: int) -> CartModel:
        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)
                await session.commit()
                return cart
            except Exception:
                await session.rollback()
                raise

    # Get a particular cart item
    async def _get_item(
        self,
        session,
        cart_id: int,
        product_id: int,
        size: Optional[str] = None
    ) -> Optional[CartItem]:

        return (
            await session.exec(
                select(CartItem).where(
                    CartItem.cart_id == cart_id,
                    CartItem.product_id == product_id,
                    CartItem.size == size
                )
            )
        ).first()

    # Calculate totals
    async def _recalculate_totals(
        self,
        session,
        cart: CartModel
    ) -> dict:

        query = (
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart.id)
        )

        results = (await session.exec(query)).all()

        subtotal = sum(
            item.quantity * product.price
            for item, product in results
        )

        discount_percentage = cart.discount_percentage or 0.0
        discount_amount = subtotal * discount_percentage / 100
        total_amount = subtotal - discount_amount

        cart.updated_at = datetime.now()

        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "total_amount": total_amount
        }

    # Change the user's cart discount
    async def discountChange(
        self,
        user_id: int,
        discount_percentage: float
    ) -> CartModel:

        if not 0 <= discount_percentage <= 100:
            raise ValueError(
                "Discount percentage must be between 0 and 100"
            )

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)

                cart.discount_percentage = discount_percentage
                cart.updated_at = datetime.now()

                session.add(cart)
                await session.commit()
                await session.refresh(cart)

                return cart

            except Exception:
                await session.rollback()
                raise

    # Add an item to the user's cart
    async def add_item(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        size: Optional[str] = None
    ) -> CartItem:

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)
                product = await session.get(Product, product_id)

                if not product:
                    raise ValueError("Product not found")

                if product.stock <= 0:
                    raise ValueError("Product is out of stock")

                item = await self._get_item(
                    session,
                    cart.id,
                    product_id,
                    size
                )

                requested_quantity = quantity

                if item:
                    requested_quantity += item.quantity

                if requested_quantity > product.stock:
                    raise ValueError(
                        f"Insufficient stock. Available stock: {product.stock}"
                    )

                if item:
                    item.quantity = requested_quantity
                else:
                    item = CartItem(
                        cart_id=cart.id,
                        product_id=product_id,
                        quantity=quantity,
                        size=size
                    )

                session.add(item)

                await self._recalculate_totals(session, cart)
                session.add(cart)

                await session.commit()
                await session.refresh(item)

                return item

            except Exception:
                await session.rollback()
                raise

    # Update the quantity of a cart item
    async def update_quantity(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
        size: Optional[str] = None
    ) -> Optional[CartItem]:

        if quantity <= 0:
            await self.remove_item(user_id, product_id, size)
            return None

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)

                item = await self._get_item(
                    session,
                    cart.id,
                    product_id,
                    size
                )

                if not item:
                    return None

                product = await session.get(Product, product_id)

                if not product:
                    raise ValueError("Product not found")

                if quantity > product.stock:
                    raise ValueError(
                        f"Insufficient stock. Available stock: {product.stock}"
                    )

                item.quantity = quantity
                session.add(item)

                await self._recalculate_totals(session, cart)
                session.add(cart)

                await session.commit()
                await session.refresh(item)

                return item

            except Exception:
                await session.rollback()
                raise

    # Remove an item from the user's cart
    async def remove_item(
        self,
        user_id: int,
        product_id: int,
        size: Optional[str] = None
    ) -> bool:

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)

                item = await self._get_item(
                    session,
                    cart.id,
                    product_id,
                    size
                )

                if not item:
                    return False

                await session.delete(item)
                await session.flush()

                await self._recalculate_totals(session, cart)
                session.add(cart)

                await session.commit()

                return True

            except Exception:
                await session.rollback()
                raise

    # Get all items in the user's cart
    async def get_items(self, user_id: int) -> list[dict]:

        async with self.db.get_session() as session:
            cart = await self._get_cart(user_id, session)

            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )

            results = (await session.exec(query)).all()

            return [
                {
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": item.quantity,
                    "size": item.size,
                    "type": (
                        product.type.value
                        if hasattr(product.type, "value")
                        else product.type
                    ),
                    "gender": product.gender,
                    "image_url": product.image_url,
                    "line_total": product.price * item.quantity
                }
                for item, product in results
            ]

    # Get the user's cart summary
    async def get_summary(self, user_id: int) -> dict:

        async with self.db.get_session() as session:
            cart = await self._get_cart(user_id, session)

            totals = await self._recalculate_totals(session, cart)

            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )

            results = (await session.exec(query)).all()

            return {
                "cart_id": cart.id,
                "user_id": user_id,
                "items": [
                    {
                        "cart_item_id": item.id,
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": item.quantity,
                        "size": item.size,
                        "price": product.price,
                        "line_total": product.price * item.quantity
                    }
                    for item, product in results
                ],
                **totals
            }

    # Clear the user's cart
    async def clear_cart(self, user_id: int) -> bool:

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)

                await session.exec(
                    delete(CartItem).where(
                        CartItem.cart_id == cart.id
                    )
                )

                await self._recalculate_totals(session, cart)
                session.add(cart)

                await session.commit()

                return True

            except Exception:
                await session.rollback()
                raise


cart = Cart(db_connection=db_connection)
CartRepository = Cart
cart_repository = cart
cart_db = cart
