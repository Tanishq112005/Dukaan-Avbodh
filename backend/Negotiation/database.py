import logging
from typing import Optional, List, Dict, Any
from sqlmodel import select

from config.database import db_connection
from Product.models import Product
from Cart.models import Cart, CartItem
from Cart.database import cart

logger = logging.getLogger(__name__)


class NegotiationDatabase:
    """
    Database access layer for negotiation.
    Provides methods to fetch product details, cart items with cost/margins,
    and update product-level discounts during interactive negotiation sessions.
    """

    def __init__(self, database_connection=None):
        self.db = database_connection or db_connection

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Fetch a single Product by its primary key ID."""
        async with self.db.get_session() as session:
            return await session.get(Product, product_id)

    async def get_cart_item(
        self,
        user_id: int,
        product_id: int,
        size: Optional[str] = None
    ) -> Optional[CartItem]:
        """Fetch a specific CartItem for a user by product ID and optional size without force-creating a cart."""
        try:
            async with self.db.get_session() as session:
                user_cart = (await session.exec(
                    select(Cart).where(Cart.user_id == user_id)
                )).first()
                if not user_cart or not user_cart.id:
                    return None

                query = select(CartItem).where(
                    CartItem.cart_id == user_cart.id,
                    CartItem.product_id == product_id,
                )
                if size is not None:
                    query = query.where(CartItem.size == size)
                item = (await session.exec(query)).first()

                # Fallback if size was provided but item was stored with size=None
                if not item and size is not None:
                    query_fallback = select(CartItem).where(
                        CartItem.cart_id == user_cart.id,
                        CartItem.product_id == product_id,
                    )
                    item = (await session.exec(query_fallback)).first()

                return item
        except Exception as e:
            logger.warning("Could not check cart item for user %s: %s", user_id, e)
            return None

    async def apply_item_discount(
        self,
        user_id: int,
        product_id: int,
        discount_percentage: float,
        discounted_price: Optional[float] = None,
        size: Optional[str] = None
    ) -> Optional[CartItem]:
        """Apply a negotiated discount percentage directly to a specific cart item."""
        return await cart.update_item_discount(
            user_id=user_id,
            product_id=product_id,
            discount_percentage=discount_percentage,
            discounted_price=discounted_price,
            size=size
        )

    async def apply_discount_to_all_items(
        self,
        user_id: int,
        discount_percentage: float
    ) -> Cart:
        """
        Apply a negotiated discount to all items in the user's cart and update the cart.
        """
        user_cart: Optional[Cart] = await cart.get_cart(user_id=user_id)
        if not user_cart or not user_cart.id:
            return user_cart

        async with self.db.get_session() as session:
            query = (
                select(CartItem, Product)
                .join(Product, CartItem.product_id == Product.id)
                .where(CartItem.cart_id == user_cart.id)
            )
            results = (await session.exec(query)).all()

            for item, product in results:
                # Cap discount at individual product margin and ceiling
                from Negotiation.utils import calculate_product_discount_limits
                p_limits = calculate_product_discount_limits(product)
                allowed_ceiling = p_limits["max_discount_percentage"]

                # Upgrade discount towards target, but preserve already negotiated higher per-product discount
                current_item_disc = float(item.discount_percentage or 0.0)
                effective_disc = min(allowed_ceiling, max(current_item_disc, float(discount_percentage)))

                from Product.models import get_base_selling_price
                public_price = get_base_selling_price(product)
                item.discount_percentage = effective_disc
                item.discounted_price = round(public_price * (1.0 - effective_disc / 100.0), 2)
                session.add(item)

            await session.commit()

        # Update cart summary totals
        return await cart.get_summary(user_id=user_id)

    async def getPoroductItemsOfCart(
        self,
        user_id: int,
        expand_quantities: bool = True
    ) -> List[Product]:
        """
        Fetch all Product models currently in the user's cart.
        """
        try:
            user_cart: Optional[Cart] = await cart.get_cart(user_id=user_id)
            if not user_cart or not user_cart.id:
                logger.info(f"No active cart found for user {user_id}")
                return []

            async with self.db.get_session() as session:
                query = (
                    select(CartItem, Product)
                    .join(Product, CartItem.product_id == Product.id)
                    .where(CartItem.cart_id == user_cart.id)
                )
                results = (await session.exec(query)).all()

                products: List[Product] = []
                for item, product in results:
                    multiplier = item.quantity if expand_quantities else 1
                    for _ in range(max(1, multiplier)):
                        products.append(product)

                return products

        except Exception as e:
            logger.exception(f"Error fetching cart products for user {user_id}: {e}")
            raise e

    # Aliases for consistent naming conventions
    get_product_items_of_cart = getPoroductItemsOfCart
    get_cart_products = getPoroductItemsOfCart

    async def get_cart_items_detailed(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch full details of all items in the cart including cost price,
        selling price, minimum profit margin, currently applied discount, and line totals.
        """
        try:
            user_cart: Optional[Cart] = await cart.get_cart(user_id=user_id)
            if not user_cart or not user_cart.id:
                return []

            async with self.db.get_session() as session:
                query = (
                    select(CartItem, Product)
                    .join(Product, CartItem.product_id == Product.id)
                    .where(CartItem.cart_id == user_cart.id)
                )
                results = (await session.exec(query)).all()

                detailed_items = []
                from Product.models import get_base_selling_price

                for item, product in results:
                    qty = item.quantity or 1
                    cost = product.cost_price or 0.0
                    price = get_base_selling_price(product)
                    margin = product.min_profit_margin_percent or 0.0
                    disc_pct = item.discount_percentage or 0.0
                    disc_price = item.discounted_price

                    if disc_price is not None and disc_price >= 0:
                        unit_selling = disc_price
                    elif disc_pct > 0:
                        unit_selling = round(price * (1.0 - disc_pct / 100.0), 2)
                    else:
                        unit_selling = price

                    min_selling_price_per_unit = ((cost * margin) / 100.0) + cost
                    min_total_selling_price = min_selling_price_per_unit * qty
                    line_total = unit_selling * qty

                    detailed_items.append({
                        "cart_item_id": item.id,
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": qty,
                        "size": item.size,
                        "cost_price": cost,
                        "original_price": price,
                        "current_price": unit_selling,
                        "discount_percentage": disc_pct,
                        "discounted_price": disc_price,
                        "min_profit_margin_percent": margin,
                        "min_selling_price_per_unit": min_selling_price_per_unit,
                        "min_total_selling_price": min_total_selling_price,
                        "line_total": line_total,
                        "product": product,
                        "cart_item": item,
                    })

                return detailed_items

        except Exception as e:
            logger.exception(f"Error fetching detailed cart items for user {user_id}: {e}")
            raise e

    async def apply_discount(
        self,
        user_id: int,
        discount_percentage: float
    ) -> Cart:
        """
        Apply a negotiated discount percentage to the user's cart items.
        """
        return await self.apply_discount_to_all_items(user_id, discount_percentage)

    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get the standard cart summary (subtotal, discount, total).
        """
        return await cart.get_summary(user_id=user_id)


# Export singleton instances
negotiationDatabase = NegotiationDatabase(db_connection)
negotiation_db = negotiationDatabase
