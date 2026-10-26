from typing import Optional, List, Dict, Any
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
            try:
                async with session.begin_nested():
                    cart = CartModel(
                        user_id=user_id,
                        discount_percentage=0.0
                    )
                    session.add(cart)
                    await session.flush()
                await session.refresh(cart)
            except Exception:
                # Concurrent insert or cart already exists, fetch existing
                cart = (
                    await session.exec(
                        select(CartModel).where(
                            CartModel.user_id == user_id
                        )
                    )
                ).first()

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

        query = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        if size is not None:
            query = query.where(CartItem.size == size)

        return (await session.exec(query)).first()

    # Calculate totals
    async def _recalculate_totals(
        self,
        session,
        cart: CartModel,
        results=None
    ) -> dict:

        if results is None:
            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )
            results = (await session.exec(query)).all()

        subtotal = 0.0
        items_discount_amount = 0.0

        for item, product in results:
            line_subtotal = float(product.price) * item.quantity
            subtotal += line_subtotal

            item_disc = float(item.discount_percentage or 0.0)
            if item.discounted_price is not None and item.discounted_price >= 0:
                item_unit_price = float(item.discounted_price)
            elif item_disc > 0:
                item_unit_price = round(float(product.price) * (1.0 - item_disc / 100.0), 2)
            else:
                item_unit_price = float(product.price)

            line_discount = max(0.0, line_subtotal - (item_unit_price * item.quantity))
            items_discount_amount += line_discount

        cart_global_discount = float(cart.discount_percentage or 0.0)
        remaining_after_items = max(0.0, subtotal - items_discount_amount)
        cart_extra_discount = remaining_after_items * (cart_global_discount / 100.0)
        total_discount_amount = round(items_discount_amount + cart_extra_discount, 2)
        total_amount = round(max(0.0, subtotal - total_discount_amount), 2)
        subtotal = round(subtotal, 2)

        cart.updated_at = datetime.now()

        return {
            "subtotal": subtotal,
            "discount_amount": total_discount_amount,
            "total_amount": total_amount
        }

    # Change the user's cart global discount
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

    # Add an item to the user's cart (supports per-product negotiated discount)
    async def add_item(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        size: Optional[str] = None,
        discount_percentage: float = 0.0,
        discounted_price: Optional[float] = None,
    ) -> CartItem:

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if discount_percentage < 0 or discount_percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")

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

                # Compute discounted unit price if discount is set
                final_discount_pct = float(discount_percentage)
                if final_discount_pct > 0 and discounted_price is None:
                    final_discounted_price = round(float(product.price) * (1.0 - final_discount_pct / 100.0), 2)
                else:
                    final_discounted_price = discounted_price

                if item:
                    item.quantity = requested_quantity
                    # If a new negotiated discount is provided on re-add, update it
                    if final_discount_pct > 0:
                        item.discount_percentage = final_discount_pct
                        item.discounted_price = final_discounted_price
                else:
                    item = CartItem(
                        cart_id=cart.id,
                        product_id=product_id,
                        quantity=quantity,
                        size=size,
                        discount_percentage=final_discount_pct,
                        discounted_price=final_discounted_price,
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

    # Update negotiated discount for a specific product in the cart
    async def update_item_discount(
        self,
        user_id: int,
        product_id: int,
        discount_percentage: float,
        discounted_price: Optional[float] = None,
        size: Optional[str] = None,
    ) -> Optional[CartItem]:
        if discount_percentage < 0 or discount_percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")

        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)
                item = await self._get_item(session, cart.id, product_id, size)

                if not item:
                    # Try without size constraint if not found with size
                    if size is not None:
                        item = await self._get_item(session, cart.id, product_id, None)
                    if not item:
                        return None

                product = await session.get(Product, product_id)
                if not product:
                    raise ValueError("Product not found")

                final_discount_pct = round(float(discount_percentage), 2)
                if discounted_price is not None:
                    final_discounted_price = round(float(discounted_price), 2)
                else:
                    final_discounted_price = round(float(product.price) * (1.0 - final_discount_pct / 100.0), 2)

                item.discount_percentage = final_discount_pct
                item.discounted_price = final_discounted_price
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

            items = []
            for item, product in results:
                disc_pct = float(item.discount_percentage or 0.0)
                if item.discounted_price is not None and item.discounted_price >= 0:
                    current_price = float(item.discounted_price)
                elif disc_pct > 0:
                    current_price = round(float(product.price) * (1.0 - disc_pct / 100.0), 2)
                else:
                    current_price = float(product.price)

                line_subtotal = round(float(product.price) * item.quantity, 2)
                line_total = round(current_price * item.quantity, 2)

                items.append({
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price": current_price,
                    "original_price": float(product.price),
                    "discount_percentage": disc_pct,
                    "discounted_price": item.discounted_price,
                    "quantity": item.quantity,
                    "size": item.size,
                    "type": (
                        product.type.value
                        if hasattr(product.type, "value")
                        else product.type
                    ),
                    "gender": product.gender,
                    "image_url": product.image_url,
                    "line_subtotal": line_subtotal,
                    "line_total": line_total,
                })

            return items

    # Get the user's cart summary
    async def get_summary(self, user_id: int) -> dict:

        async with self.db.get_session() as session:
            cart = await self._get_cart(user_id, session)

            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == cart.id)
            )

            results = (await session.exec(query)).all()
            totals = await self._recalculate_totals(session, cart, results=results)

            summary_items = []
            for item, product in results:
                disc_pct = float(item.discount_percentage or 0.0)
                if item.discounted_price is not None and item.discounted_price >= 0:
                    current_price = float(item.discounted_price)
                elif disc_pct > 0:
                    current_price = round(float(product.price) * (1.0 - disc_pct / 100.0), 2)
                else:
                    current_price = float(product.price)

                summary_items.append({
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "name": product.name,
                    "quantity": item.quantity,
                    "size": item.size,
                    "price": current_price,
                    "original_price": float(product.price),
                    "discount_percentage": disc_pct,
                    "discounted_price": item.discounted_price,
                    "line_total": round(current_price * item.quantity, 2),
                })

            effective_discount_pct = (
                round((totals["discount_amount"] / totals["subtotal"]) * 100.0, 2)
                if totals["subtotal"] > 0
                else 0.0
            )

            return {
                "cart_id": cart.id,
                "user_id": user_id,
                "items": summary_items,
                "effective_discount_percentage": effective_discount_pct,
                **totals
            }

    # Bulk sync user cart items in a single transaction (avoids N+1 add_item queries)
    async def sync_items(self, user_id: int, items: list) -> bool:
        async with self.db.get_session() as session:
            try:
                cart = await self._get_cart(user_id, session)

                # Clear existing items first
                await session.exec(delete(CartItem).where(CartItem.cart_id == cart.id))

                if items:
                    raw_ids = [
                        int(item["id"] if "id" in item else item["product_id"])
                        for item in items
                        if ("id" in item or "product_id" in item)
                    ]

                    if raw_ids:
                        products_res = await session.exec(select(Product).where(Product.id.in_(raw_ids)))
                        product_map = {p.id: p for p in products_res.all()}

                        new_cart_items = []
                        for item in items:
                            pid = int(item.get("id") or item.get("product_id"))
                            product = product_map.get(pid)
                            if not product or product.stock <= 0:
                                continue

                            qty = min(int(item.get("qty") or item.get("quantity") or 1), product.stock)
                            disc_pct = float(item.get("discount_percentage", 0.0) or 0.0)
                            disc_price = item.get("discounted_price")
                            if disc_price is not None:
                                disc_price = float(disc_price)
                            elif disc_pct > 0:
                                disc_price = round(float(product.price) * (1.0 - disc_pct / 100.0), 2)

                            new_cart_items.append(CartItem(
                                cart_id=cart.id,
                                product_id=pid,
                                quantity=qty,
                                size=item.get("size"),
                                discount_percentage=disc_pct,
                                discounted_price=disc_price,
                            ))

                        if new_cart_items:
                            session.add_all(new_cart_items)

                await self._recalculate_totals(session, cart)
                session.add(cart)

                await session.commit()
                return True

            except Exception:
                await session.rollback()
                raise

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
cartRepository = cart
cart_db = cart
