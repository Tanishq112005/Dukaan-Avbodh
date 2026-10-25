from typing import Optional, List
from sqlmodel import select
from sqlalchemy.orm import selectinload
from config.database import db_connection
from Cart.database import cart
from Cart.models import Cart
from Order.models import Order 
from Product.models import Product
from Order.models import PaymentStatus


class OrderRepository:
    def __init__(self, db_connection=None):
        from config.database import db_connection as default_db
        self.db = db_connection or default_db
        
    ## Getting all the User Order 
    async def getUsersAllOrder(self, user_id: int) -> List[Order]:
        async with self.db.get_session() as session:
            result = await session.exec(
                select(Order).where(Order.user_id == user_id)
            )
            return result.all()
    
    ## Update Payment Status of the User Order 
    async def updatePaymentStatus(self, order_id: int, status: str) -> Optional[Order]:
        async with self.db.get_session() as session:
            try:
                result = await session.exec(
                    select(Order).where(Order.id == order_id)
                )
                order: Order = result.first()
                if order is not None:
                    order.payment_status = status
                    session.add(order)
                    await session.commit()
                    await session.refresh(order)
                return order
            except Exception as e:
                await session.rollback()
                raise e
            
    ## Creating the Order 
    async def createOrder(self, user_id: int) -> Order:
        itemsOfCart = await cart.get_items(user_id=user_id)
        if not itemsOfCart:
            raise ValueError("Cart is empty. Cannot create an order.")

        cart_obj = await cart.get_cart(user_id=user_id)
        cart_discount = cart_obj.discount_percentage if cart_obj else 0.0

        async with self.db.get_session() as session:
            try:
                total_amount = 0.0
                orders = []

                for item in itemsOfCart:
                    product_id = item.get("product_id") if isinstance(item, dict) else item.product_id
                    quantity = item.get("quantity") if isinstance(item, dict) else item.quantity

                    result = await session.exec(
                        select(Product).where(Product.id == product_id)
                    )
                    product = result.first()

                    if product is None:
                        raise ValueError(f"Product with ID {product_id} not found")

                    if product.stock < quantity:
                        raise ValueError(f"Insufficient stock for {product.name}")

                    item_total = product.price * quantity
                    total_amount += item_total

                    order = Order(
                        product_id=product.id,
                        user_id=user_id,
                        total_amount=item_total,
                        payment_status=PaymentStatus.PENDING,
                    )

                    orders.append(order)

                session.add_all(orders)
                await session.commit()

                for order in orders:
                    await session.refresh(order)

                return orders[0]

            except Exception:
                await session.rollback()
                raise


Order = OrderRepository
orderRepository = OrderRepository(db_connection=db_connection)
order_repository = orderRepository
OrderDatabase = OrderRepository
order_db = orderRepository
