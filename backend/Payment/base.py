from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class PaymentGatewayInterface(ABC):
    """
    Abstract interface for all payment gateways.
    Follows Strategy Pattern & Dependency Inversion Principle,
    allowing Dukaan to seamlessly plug in Razorpay, Stripe, PayPal, or any new gateway.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the unique name of the payment provider (e.g. 'razorpay', 'stripe')."""
        pass

    @abstractmethod
    async def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a payment order with the gateway.
        Amount must be provided in smallest currency unit (e.g. paise for INR, cents for USD).
        """
        pass

    @abstractmethod
    async def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        description: str = "Dukaan Order Payment",
        customer: Optional[Dict[str, Any]] = None,
        notes: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a hosted payment link for customers (e.g. for chat agent checkout).
        """
        pass

    @abstractmethod
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Cryptographically verifies the authenticity of client-submitted payment completion credentials.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Validates webhook payload authenticity against gateway HMAC secret.
        """
        pass

    @abstractmethod
    async def fetch_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches the current real-time status of a payment by its gateway payment ID.
        """
        pass

    @abstractmethod
    async def fetch_payment_link_status(self, link_id: str) -> Dict[str, Any]:
        """
        Fetches the current real-time status of a payment link by its gateway link ID.
        """
        pass
