import os
import hmac
import hashlib
import asyncio
import logging
from typing import Optional, Dict, Any

from Payment.base import PaymentGatewayInterface

logger = logging.getLogger(__name__)


class RazorpayPaymentGateway(PaymentGatewayInterface):
    """
    Concrete implementation of PaymentGatewayInterface using the official 'razorpay' library.
    Handles order creation, payment link generation, HMAC signature validation,
    and webhook authenticity checks.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self._key_id = key_id or os.getenv("RAZORPAY_KEY_ID", "rzp_test_TWV2ichCwzRcvo")
        self._key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET", "9Ew8lMz1DUumk4hYVPBbf4dd")
        self._webhook_secret = webhook_secret or os.getenv("RAZORPAY_WEBHOOK_SECRET", self._key_secret)

        try:
            import razorpay
            self._client = razorpay.Client(auth=(self._key_id, self._key_secret))
        except Exception as e:
            logger.error("Failed to initialize Razorpay client: %s", e)
            self._client = None

    @property
    def provider_name(self) -> str:
        return "razorpay"

    @property
    def client_key_id(self) -> str:
        """Returns the public key ID safe for frontend checkout widgets."""
        return self._key_id

    @property
    def client(self):
        return self._client

    async def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates a Razorpay payment order."""
        if not self._client:
            raise RuntimeError("Razorpay client is not initialized.")

        if amount < 100:
            raise ValueError("Amount must be at least 100 paise (1 INR).")

        order_data = {
            "amount": int(amount),
            "currency": currency or "INR",
            "receipt": receipt or f"receipt_{int(asyncio.get_event_loop().time() * 1000)}",
        }
        if notes:
            order_data["notes"] = {str(k): str(v) for k, v in notes.items()}

        try:
            order = await asyncio.to_thread(self._client.order.create, order_data)
            return order
        except Exception as e:
            logger.error("Razorpay order creation failed: %s", e)
            raise

    async def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        description: str = "Dukaan Order Payment",
        customer: Optional[Dict[str, Any]] = None,
        notes: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a hosted Razorpay payment link."""
        if not self._client:
            raise RuntimeError("Razorpay client is not initialized.")

        payload = {
            "amount": int(amount),
            "currency": currency or "INR",
            "accept_partial": False,
            "description": description,
        }

        if customer:
            cust_dict = {
                "name": customer.get("name") or "Valued Customer",
                "email": customer.get("email") or "client@dukaan.store",
            }
            contact = customer.get("contact")
            # Razorpay requires valid contact format; recurring dummy digits (e.g. 9999999999) are rejected
            if contact and len(contact) >= 10 and len(set(contact.replace("+", "").replace("-", ""))) > 1:
                cust_dict["contact"] = contact
            payload["customer"] = cust_dict

        if callback_url:
            payload["callback_url"] = callback_url
            payload["callback_method"] = "get"

        if notes:
            payload["notes"] = {str(k): str(v) for k, v in notes.items()}

        try:
            link = await asyncio.to_thread(self._client.payment_link.create, payload)
            return link
        except Exception as e:
            logger.error("Razorpay payment link creation failed: %s", e)
            raise

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verifies standard Razorpay checkout signature:
        HMAC-SHA256 of '{order_id}|{payment_id}' using the key secret.
        """
        if not order_id or not payment_id or not signature:
            return False

        # Attempt verification using official razorpay utility
        if self._client:
            try:
                self._client.utility.verify_payment_signature({
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                })
                return True
            except Exception:
                pass

        # Fallback to direct HMAC-SHA256 check
        msg = f"{order_id}|{payment_id}"
        expected = hmac.new(
            self._key_secret.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature: str,
        secret: Optional[str] = None,
    ) -> bool:
        """Verifies webhook signature using Razorpay webhook secret."""
        effective_secret = secret or self._webhook_secret
        if not signature or not effective_secret:
            return False

        # Attempt verification using official utility if available
        if self._client:
            try:
                self._client.utility.verify_webhook_signature(
                    body_bytes.decode("utf-8") if isinstance(body_bytes, bytes) else str(body_bytes),
                    signature,
                    effective_secret,
                )
                return True
            except Exception:
                pass

        # Direct HMAC-SHA256 calculation
        expected = hmac.new(
            effective_secret.encode("utf-8"),
            body_bytes if isinstance(body_bytes, bytes) else body_bytes.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def fetch_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Fetches status of a specific payment ID."""
        if not self._client:
            raise RuntimeError("Razorpay client is not initialized.")
        return await asyncio.to_thread(self._client.payment.fetch, payment_id)

    async def fetch_payment_link_status(self, link_id: str) -> Dict[str, Any]:
        """Fetches status of a specific payment link ID."""
        if not self._client:
            raise RuntimeError("Razorpay client is not initialized.")
        return await asyncio.to_thread(self._client.payment_link.fetch, link_id)
