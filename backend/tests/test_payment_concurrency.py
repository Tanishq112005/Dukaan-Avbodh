import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from Order.locks import ProductLockManager
from Order.database import InsufficientStockError
from Payment.base import PaymentGatewayInterface
from Payment.factory import PaymentGatewayFactory
from Payment.providers.razorpay_provider import RazorpayPaymentGateway
from Payment.schemas import PaymentVerifyRequest, PaymentOrderCreateRequest


class TestPaymentAndConcurrency(unittest.IsolatedAsyncioTestCase):

    async def test_product_lock_manager_concurrency(self):
        """Verify that concurrent tasks acquire locks mutually exclusively and without deadlock."""
        lock_mgr = ProductLockManager(ttl_seconds=5, acquire_timeout=2.0)
        execution_order = []

        async def worker(worker_id: int, product_ids: list):
            async with lock_mgr.acquire_locks(product_ids):
                execution_order.append(f"start_{worker_id}")
                await asyncio.sleep(0.05)
                execution_order.append(f"end_{worker_id}")

        # Both workers contend for overlapping products [1, 2] in different initial orders
        task1 = asyncio.create_task(worker(1, [1, 2]))
        task2 = asyncio.create_task(worker(2, [2, 1]))

        await asyncio.gather(task1, task2)

        # Confirm non-interleaved critical section execution
        self.assertEqual(len(execution_order), 4)
        first_worker = execution_order[0].split("_")[1]
        self.assertEqual(execution_order[1], f"end_{first_worker}")

    def test_payment_gateway_factory_extensibility(self):
        """Verify that the factory supports registering multiple gateways (Strategy Pattern)."""
        factory = PaymentGatewayFactory()

        # 1. Default razorpay gateway
        rzp = factory.get_gateway("razorpay")
        self.assertEqual(rzp.provider_name, "razorpay")

        # 2. Add custom Stripe / mock gateway
        class MockStripeGateway(PaymentGatewayInterface):
            @property
            def provider_name(self) -> str:
                return "stripe"
            async def create_order(self, *args, **kwargs):
                return {"id": "ch_mock_123"}
            async def create_payment_link(self, *args, **kwargs):
                return {"id": "pl_mock_123"}
            def verify_payment_signature(self, *args, **kwargs):
                return True
            def verify_webhook_signature(self, *args, **kwargs):
                return True
            async def fetch_payment_status(self, *args, **kwargs):
                return {"status": "paid"}
            async def fetch_payment_link_status(self, *args, **kwargs):
                return {"status": "paid"}

        factory.register("stripe", MockStripeGateway())
        stripe_gw = factory.get_gateway("stripe")
        self.assertEqual(stripe_gw.provider_name, "stripe")

    def test_razorpay_signature_verification(self):
        """Verify cryptographic HMAC-SHA256 signature verification."""
        gateway = RazorpayPaymentGateway(
            key_id="rzp_test_sample",
            key_secret="test_secret_key_123",
        )

        import hmac
        import hashlib

        order_id = "order_sample_001"
        payment_id = "pay_sample_001"
        valid_sig = hmac.new(
            b"test_secret_key_123",
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Valid signature must pass
        self.assertTrue(gateway.verify_payment_signature(order_id, payment_id, valid_sig))

        # Tampered signature must fail
        self.assertFalse(gateway.verify_payment_signature(order_id, payment_id, "tampered_signature"))

    def test_razorpay_webhook_signature_verification(self):
        """Verify webhook payload signature verification."""
        gateway = RazorpayPaymentGateway(
            key_id="rzp_test_sample",
            key_secret="test_secret_key_123",
            webhook_secret="webhook_secret_xyz",
        )

        import hmac
        import hashlib

        payload_bytes = b'{"event": "payment.captured", "payload": {}}'
        valid_webhook_sig = hmac.new(
            b"webhook_secret_xyz",
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        self.assertTrue(gateway.verify_webhook_signature(payload_bytes, valid_webhook_sig))
        self.assertFalse(gateway.verify_webhook_signature(payload_bytes, "invalid_sig"))


if __name__ == "__main__":
    unittest.main()
