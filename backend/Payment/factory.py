import os
import logging
from typing import Dict, Optional, Type, Union

from Payment.base import PaymentGatewayInterface
from Payment.providers.razorpay_provider import RazorpayPaymentGateway

logger = logging.getLogger(__name__)


class PaymentGatewayFactory:
    """
    Factory & Registry for Payment Gateways.
    Allows easy addition and switching of payment gateways (Razorpay, Stripe, PayPal, etc.)
    without modifying core order or business logic (Open/Closed Principle).
    """

    def __init__(self):
        self._gateways: Dict[str, Union[PaymentGatewayInterface, Type[PaymentGatewayInterface]]] = {}
        # Register default Razorpay gateway
        self.register("razorpay", RazorpayPaymentGateway())

    def register(
        self,
        provider_name: str,
        gateway: Union[PaymentGatewayInterface, Type[PaymentGatewayInterface]],
    ):
        """Registers a payment gateway instance or class."""
        self._gateways[provider_name.lower()] = gateway
        logger.info("Registered payment provider '%s'", provider_name)

    def get_gateway(self, provider_name: Optional[str] = None) -> PaymentGatewayInterface:
        """
        Retrieves the requested payment gateway, or falls back to DEFAULT_PAYMENT_PROVIDER
        or 'razorpay'.
        """
        default_provider = os.getenv("DEFAULT_PAYMENT_PROVIDER", "razorpay").lower()
        provider = (provider_name or default_provider).lower()

        gateway = self._gateways.get(provider)
        if not gateway:
            available = list(self._gateways.keys())
            raise ValueError(
                f"Unsupported payment provider '{provider}'. Available providers: {available}"
            )

        # If registered as a class, instantiate it
        if isinstance(gateway, type):
            instance = gateway()
            self._gateways[provider] = instance
            return instance

        return gateway


payment_gateway_factory = PaymentGatewayFactory()
