import logging
from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlalchemy.orm import selectinload

from config.database import db_connection
from Order.models import Order as OrderModel, PaymentStatus
from Order.locks import product_lock_manager
from Product.models import Product

logger = logging.getLogger(__name__)


class InsufficientStockError(ValueError):
    """Raised when one or more products do not have sufficient inventory."""
    pass


class OrderRepository:
    def __init__(self, db_connection_instance=None):
        from config.database import db_connection as default_db
        self.db = db_connection_instance or default_db
        self.lock_manager = product_lock_manager

    async def getUsersAllOrder(self, user_id: int) -> List[OrderModel]:
        """Fetch all orders for a specific user with product data loaded."""
        async with self.db.get_session() as session:
            result = await session.exec(
                select(OrderModel)
                .options(selectinload(OrderModel.product))
                .where(OrderModel.user_id == user_id)
                .order_by(OrderModel.created_at.desc())
            )
            return result.all()

    async def get_order_by_id(self, order_id: int) -> Optional[OrderModel]:
        """Fetch a single order by its ID with product data loaded."""
        async with self.db.get_session() as session:
            result = await session.exec(
                select(OrderModel)
                .options(selectinload(OrderModel.product))
                .where(OrderModel.id == order_id)
            )
            return result.first()

    async def get_orders_by_gateway_id(self, gateway_order_id: str) -> List[OrderModel]:
        """Fetch orders associated with an external payment gateway order ID."""
        async with self.db.get_session() as session:
            result = await session.exec(
                select(OrderModel)
                .options(selectinload(OrderModel.product))
                .where(OrderModel.gateway_order_id == gateway_order_id)
            )
            return result.all()

    async def updatePaymentStatus(self, order_id: int, status: str) -> Optional[OrderModel]:
        """Update payment status of a single order."""
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(OrderModel).where(OrderModel.id == order_id)
                )
                order: OrderModel = result.first()

                if order is not None:
                    order.payment_status = status
                    session.add(order)
                    await session.commit()
                    await session.refresh(order)

                return order

            except Exception as e:
                await session.rollback()
                logger.error("Failed to update payment status for order %s: %s", order_id, e)
                raise e

    async def confirm_order_payment(
        self,
        gateway_order_id: Optional[str] = None,
        gateway_payment_id: Optional[str] = None,
        user_id: Optional[int] = None,
        order_id: Optional[int] = None,
    ) -> List[OrderModel]:
        """
        Marks pending orders as PAID/COMPLETED upon payment gateway verification.
        Stock was already safely reserved during order creation.
        """
        async with self.db.get_session() as session:
            try:
                query = select(OrderModel).options(selectinload(OrderModel.product))
                if gateway_order_id:
                    query = query.where(OrderModel.gateway_order_id == gateway_order_id)
                elif order_id:
                    query = query.where(OrderModel.id == order_id)
                elif user_id:
                    query = query.where(OrderModel.user_id == user_id).where(
                        OrderModel.payment_status.in_([
                            PaymentStatus.PENDING,
                            PaymentStatus.PROCESSING,
                        ])
                    )
                else:
                    return []

                results = (await session.exec(query)).all()
                updated_orders = []

                for order in results:
                    order.payment_status = PaymentStatus.PAID
                    if gateway_payment_id:
                        order.gateway_payment_id = gateway_payment_id
                    session.add(order)
                    updated_orders.append(order)

                if updated_orders:
                    await session.commit()
                    for o in updated_orders:
                        await session.refresh(o)

                    # Dispatch order confirmation receipt to RabbitMQ
                    try:
                        from Order.notifications import enqueue_order_confirmation_notification
                        import asyncio
                        asyncio.create_task(
                            enqueue_order_confirmation_notification(
                                orders=updated_orders,
                                user_id=user_id,
                            )
                        )
                    except Exception as notif_err:
                        logger.warning('Could not trigger order notification: %s', notif_err)

                return updated_orders
            except Exception as e:
                await session.rollback()
                logger.error("Failed to confirm order payment: %s", e)
                raise

    async def cancel_order_with_lock(self, order_id: int, reason: str = "payment_failed") -> Optional[OrderModel]:
        """
        Cancels an order and safely restores the reserved product inventory using distributed locks.
        """
        async with self.db.get_session() as session:
            result = await session.exec(select(OrderModel).where(OrderModel.id == order_id))
            order = result.first()
            if not order:
                return None

            # Only restore stock if order was pending or processing
            if order.payment_status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
                return order

            product_id = order.product_id
            quantity = order.quantity

        # Re-acquire lock to safely restore stock
        async with self.lock_manager.acquire_locks([product_id]):
            async with self.db.get_session() as session:
                try:
                    p_res = await session.exec(
                        select(Product).where(Product.id == product_id).with_for_update()
                    )
                    product = p_res.first()
                    if product:
                        product.stock += quantity
                        session.add(product)

                    o_res = await session.exec(select(OrderModel).where(OrderModel.id == order_id))
                    ord_obj = o_res.first()
                    if ord_obj:
                        ord_obj.payment_status = PaymentStatus.CANCELLED
                        session.add(ord_obj)

                    await session.commit()
                    await session.refresh(ord_obj)
                    return ord_obj
                except Exception as e:
                    await session.rollback()
                    logger.error("Failed to cancel order %s and restore stock: %s", order_id, e)
                    raise

    async def create_order_with_lock(
        self,
        user_id: int,
        items: Optional[List[Dict[str, Any]]] = None,
        discount_percentage: float = 0.0,
        gateway_order_id: Optional[str] = None,
        gateway_link_id: Optional[str] = None,
        payment_link_url: Optional[str] = None,
        provider: str = "razorpay",
    ) -> List[OrderModel]:
        """
        Atomically creates order rows and reserves inventory under strict concurrency locks.
        
        Concurrency Architecture:
        1. Multi-product distributed lock (via Redis + local fallback) with sorted product IDs.
        2. Database transaction with SELECT ... FOR UPDATE (pessimistic row lock in SQL).
        3. Strict inventory check: if any product has insufficient stock, the transaction
           aborts immediately and raises InsufficientStockError.
        4. Stock is decremented within the same atomic ACID transaction.
        5. Supports individual product negotiated discounts.
        """
        # If no explicit items provided, read from user's active cart
        if items is None:
            from Cart.database import cart
            cart_items = await cart.get_items(user_id=user_id)
            if not cart_items:
                raise ValueError("Cart is empty. Cannot create an order.")

            cart_obj = await cart.get_cart(user_id=user_id)
            if cart_obj and cart_obj.discount_percentage:
                discount_percentage = max(discount_percentage, cart_obj.discount_percentage)

            items = [
                {
                    "product_id": it.get("product_id") if isinstance(it, dict) else it.product_id,
                    "quantity": it.get("quantity") if isinstance(it, dict) else it.quantity,
                    "discount_percentage": float(it.get("discount_percentage", 0.0) or 0.0) if isinstance(it, dict) else float(getattr(it, "discount_percentage", 0.0) or 0.0),
                }
                for it in cart_items
            ]

        if not items:
            raise ValueError("No items provided for order checkout.")

        # Aggregate requested quantities and per-item discounts per product_id
        product_quantities: Dict[int, int] = {}
        product_discounts: Dict[int, float] = {}
        for it in items:
            pid = int(it.get("product_id") or it.get("id"))
            qty = int(it.get("quantity") or it.get("qty") or 1)
            if qty <= 0:
                continue
            product_quantities[pid] = product_quantities.get(pid, 0) + qty
            it_disc = float(it.get("discount_percentage", 0.0) or 0.0)
            product_discounts[pid] = max(product_discounts.get(pid, 0.0), it_disc, discount_percentage)

        if not product_quantities:
            raise ValueError("Invalid item quantities.")

        product_ids = sorted(list(product_quantities.keys()))

        # 1. Acquire distributed lock across all requested product IDs
        async with self.lock_manager.acquire_locks(product_ids):
            # 2. Open ACID transaction with row-level pessimistic locks (SELECT FOR UPDATE)
            async with self.db.get_session() as session:
                try:
                    stmt = (
                        select(Product)
                        .where(Product.id.in_(product_ids))
                        .with_for_update()
                    )
                    products_res = await session.exec(stmt)
                    product_map: Dict[int, Product] = {p.id: p for p in products_res.all()}

                    # Verify product existence and inventory availability
                    for pid, requested_qty in product_quantities.items():
                        product = product_map.get(pid)
                        if not product:
                            raise ValueError(f"Product with ID {pid} not found.")

                        if product.stock < requested_qty:
                            raise InsufficientStockError(
                                f"Insufficient stock for '{product.name}'. "
                                f"Available: {product.stock}, Requested: {requested_qty}."
                            )

                    # Reserve/decrement stock and build orders
                    orders: List[OrderModel] = []

                    for pid, requested_qty in product_quantities.items():
                        product = product_map[pid]
                        # Atomically decrement inventory
                        product.stock -= requested_qty
                        session.add(product)

                        from Product.models import get_base_selling_price
                        item_disc = product_discounts.get(pid, discount_percentage)
                        item_discount_factor = max(0.0, 1.0 - (item_disc / 100.0))

                        item_base_price = get_base_selling_price(product)
                        item_subtotal = item_base_price * requested_qty
                        item_final_amount = round(item_subtotal * item_discount_factor, 2)

                        order = OrderModel(
                            product_id=product.id,
                            user_id=user_id,
                            quantity=requested_qty,
                            gateway_order_id=gateway_order_id,
                            gateway_link_id=gateway_link_id,
                            payment_link_url=payment_link_url,
                            provider=provider,
                            payment_status=PaymentStatus.PENDING,
                            total_amount=item_final_amount,
                            discount_applied=item_disc,
                        )
                        orders.append(order)

                    session.add_all(orders)
                    await session.commit()

                    for order in orders:
                        await session.refresh(order)

                    logger.info(
                        "Created %d order items with stock lock reservation for user %s (Gateway Order: %s)",
                        len(orders),
                        user_id,
                        gateway_order_id,
                    )
                    return orders

                except Exception as exc:
                    await session.rollback()
                    logger.warning("Order creation with lock failed: %s", exc)
                    raise

    async def createOrder(self, user_id: int) -> OrderModel:
        """
        Backward-compatible method: creates order from cart using lock-based reservation.
        Returns the primary order created.
        """
        orders = await self.create_order_with_lock(user_id=user_id)
        return orders[0] if orders else None


# Aliases & singleton instances
Order = OrderRepository
orderRepository = OrderRepository(db_connection_instance=db_connection)
order_repository = orderRepository
OrderDatabase = OrderRepository
order_db = orderRepository
