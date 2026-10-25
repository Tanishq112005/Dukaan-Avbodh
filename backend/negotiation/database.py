import logging
from typing import Optional, List, Dict, Any
from sqlmodel import select

from config.database import db_connection
from models.product import Product
from models.cart import Cart, CartItem
from repositories.cart import cart

logger = logging.getLogger(__name__)


class NegotiationDatabase:
    """
    Database access layer for negotiation.
    Provides methods to fetch cart products, cart items with cost/margins,
    and update cart discounts during negotiation sessions.
    """

    def __init__(self, database_connection=None):
        self.db = database_connection or db_connection

    async def getPoroductItemsOfCart(
        self,
        user_id: int,
        expand_quantities: bool = True
    ) -> List[Product]:
        """
        Fetch all Product models currently in the user's cart.

        Args:
            user_id: The ID of the user.
            expand_quantities: If True, duplicates the Product object by its quantity
                               so tools like maximumDiscountPossible calculate margin
                               and cost across all units. If False, returns unique products.

        Returns:
            List[Product]: List of product models in the cart.
        """
        try:
            # 1. Fetch user's cart using cart repository
            user_cart: Optional[Cart] = await cart.get_cart(user_id=user_id)
            if not user_cart or not user_cart.id:
                logger.info(f"No active cart found for user {user_id}")
                return []

            # 2. Query CartItem joined with Product using self.db.get_session()
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
        selling price, minimum profit margin, and line totals.
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
                for item, product in results:
                    qty = item.quantity or 1
                    cost = product.cost_price or 0.0
                    price = product.price or 0.0
                    margin = product.min_profit_margin_percent or 0.0

                    min_selling_price_per_unit = ((cost * margin) / 100.0) + cost
                    min_total_selling_price = min_selling_price_per_unit * qty
                    line_total = price * qty

                    detailed_items.append({
                        "cart_item_id": item.id,
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": qty,
                        "size": item.size,
                        "cost_price": cost,
                        "selling_price": price,
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
        Apply a negotiated discount percentage to the user's cart.
        """
        return await cart.discountChange(user_id, discount_percentage)

    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get the standard cart summary (subtotal, discount, total).
        """
        return await cart.get_summary(user_id=user_id)


# Export singleton instances
negotiationDatabase = NegotiationDatabase(db_connection)
negotiation_db = negotiationDatabase
