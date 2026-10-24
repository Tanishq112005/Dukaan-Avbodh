from typing import Optional
from datetime import datetime
from sqlmodel import select, delete
from models.cart import Cart as CartModel, CartItem
from models.product import Product
from base_repository import BaseRepository
from models import Cart

class Cart(BaseRepository[Cart]):

    def __init__(self, user_id: int, db_connection):
        self.user_id = user_id
        self.db = db_connection
        self.discount_percentage = 0.0

    # Get the user's cart or create one if it doesn't exist
    async def _get_cart(self, session) -> CartModel:
        cart = (
            await session.exec(
                select(CartModel).where(
                    CartModel.user_id == self.user_id
                )
            )
        ).first()

        if cart:
            return cart

        cart = CartModel(user_id=self.user_id)
        session.add(cart)
        await session.flush()
        await session.refresh(cart)

        return cart

    # Get a specific cart item by product ID and size
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

    # Calculate cart subtotal, discount, and total
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

        cart.updated_at = datetime.utcnow()

        discount_amount = (
            subtotal * self.discount_percentage / 100
        )
        total_amount = subtotal - discount_amount

        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "total_amount": total_amount
        }

    # Update the cart discount percentage
    def discountChange(self, discount_percentage: float):
        if not 0 <= discount_percentage <= 100:
            raise ValueError(
                "Discount percentage must be between 0 and 100"
            )

        self.discount_percentage = discount_percentage

    # Add an item or increase its quantity after checking stock
    async def add_item(
        self,
        product_id: int,
        quantity: int = 1,
        size: Optional[str] = None
    ) -> CartItem:
        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero"
            )

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(session)

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
                        f"Insufficient stock. "
                        f"Available stock: {product.stock}"
                    )

                if item:
                    item.quantity = requested_quantity
                    session.add(item)
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

    # Update quantity after checking available stock
    async def update_quantity(
        self,
        product_id: int,
        quantity: int,
        size: Optional[str] = None
    ) -> Optional[CartItem]:
        if quantity <= 0:
            await self.remove_item(product_id, size)
            return None

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(session)

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

                if product.stock <= 0:
                    raise ValueError("Product is out of stock")

                if quantity > product.stock:
                    raise ValueError(
                        f"Insufficient stock. "
                        f"Available stock: {product.stock}"
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

    # Remove a specific item from the cart
    async def remove_item(
        self,
        product_id: int,
        size: Optional[str] = None
    ) -> bool:
        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(session)

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

    # Get all cart items with their product details
    async def get_items(self) -> list[dict]:
        async with self.db.get_session() as session:
            cart = await self._get_cart(session)

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

    # Get the complete cart summary
    async def get_summary(self) -> dict:
        async with self.db.get_session() as session:
            cart = await self._get_cart(session)

            totals = await self._recalculate_totals(
                session,
                cart
            )

            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )

            results = (await session.exec(query)).all()

            return {
                "cart_id": cart.id,
                "user_id": self.user_id,
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

    # Remove every item from the cart
    async def clear_cart(self) -> bool:
        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(session)

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