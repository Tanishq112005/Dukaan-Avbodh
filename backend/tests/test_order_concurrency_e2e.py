import asyncio
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from Order.database import OrderRepository, InsufficientStockError
from Order.models import PaymentStatus, Order as OrderModel
from Product.models import Product, ProductType


class MockSession:
    """Mock database session simulating transactional SELECT ... FOR UPDATE and commits."""
    def __init__(self, db_state):
        self.db_state = db_state
        self.staged = []

    async def exec(self, stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from \"order\"" in stmt_str or "from order" in stmt_str:
            orders = [self.db_state["order"]] if "order" in self.db_state else []
            mock_result.all.return_value = orders
            mock_result.first.return_value = orders[0] if orders else None
        else:
            products = [self.db_state["product"]] if "product" in self.db_state else []
            mock_result.all.return_value = products
            mock_result.first.return_value = products[0] if products else None
        return mock_result

    def add(self, obj):
        self.staged.append(obj)

    def add_all(self, objects):
        self.staged.extend(objects)

    async def commit(self):
        pass

    async def refresh(self, obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 101

    async def rollback(self):
        pass

    async def close(self):
        pass


class MockDbConnection:
    def __init__(self, product, order=None):
        self.db_state = {"product": product}
        if order:
            self.db_state["order"] = order

    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def get_session(self):
        yield MockSession(self.db_state)


class TestOrderConcurrencyE2E(unittest.IsolatedAsyncioTestCase):

    async def test_concurrent_buyers_limited_stock(self):
        """
        Scenario:
        A luxury shirt has remaining stock = 2.
        Buyer 1 attempts to buy 2 shirts.
        Buyer 2 simultaneously attempts to buy 2 shirts.
        With concurrency locking, exactly one buyer succeeds (reserving 2 units, stock becomes 0),
        and the other buyer fails with InsufficientStockError.
        No overselling occurs.
        """
        shirt = Product(
            id=999,
            name="Classic Oxford Cotton Shirt",
            price=2500.0,
            stock=2,
            type=ProductType.SHIRT,
        )

        mock_db = MockDbConnection(shirt)
        order_repo = OrderRepository(db_connection_instance=mock_db)

        results = []
        errors = []

        async def buyer_checkout(user_id: int, quantity: int):
            try:
                orders = await order_repo.create_order_with_lock(
                    user_id=user_id,
                    items=[{"product_id": 999, "quantity": quantity}],
                    discount_percentage=10.0,
                    provider="razorpay",
                )
                results.append((user_id, orders))
            except InsufficientStockError as e:
                errors.append((user_id, str(e)))

        # Run both buyers concurrently
        buyer1_task = asyncio.create_task(buyer_checkout(1001, 2))
        buyer2_task = asyncio.create_task(buyer_checkout(1002, 2))

        await asyncio.gather(buyer1_task, buyer2_task)

        # Assertions
        # 1. Exactly one buyer succeeded
        self.assertEqual(len(results), 1, "Exactly one buyer should succeed")
        # 2. Exactly one buyer failed with InsufficientStockError
        self.assertEqual(len(errors), 1, "The competing buyer must receive InsufficientStockError")
        # 3. Final stock must be 0 (no overselling below 0)
        self.assertEqual(shirt.stock, 0, "Stock must decrement from 2 to 0 without going negative")

        successful_user, created_orders = results[0]
        self.assertEqual(len(created_orders), 1)
        self.assertEqual(created_orders[0].quantity, 2)
        self.assertEqual(created_orders[0].payment_status, PaymentStatus.PENDING)
        self.assertEqual(created_orders[0].total_amount, 4500.0)  # 2500 * 2 with 10% discount

    async def test_order_stock_restoration_on_cancellation(self):
        """Verify that cancelling an order restores the reserved stock under lock."""
        shirt = Product(
            id=998,
            name="Silk Evening Shirt",
            price=4000.0,
            stock=0,  # 2 units were already reserved
            type=ProductType.SHIRT,
        )

        existing_order = OrderModel(
            id=77,
            product_id=998,
            user_id=1001,
            quantity=2,
            payment_status=PaymentStatus.PENDING,
            total_amount=8000.0,
        )

        mock_db = MockDbConnection(shirt, existing_order)
        order_repo = OrderRepository(db_connection_instance=mock_db)
        cancelled_order = await order_repo.cancel_order_with_lock(77)

        # Stock should be restored from 0 back to 2
        self.assertEqual(shirt.stock, 2)
        self.assertEqual(cancelled_order.payment_status, PaymentStatus.CANCELLED)


if __name__ == "__main__":
    unittest.main()
