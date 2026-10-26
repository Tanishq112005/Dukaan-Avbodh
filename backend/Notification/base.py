from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class NotificationType(str, Enum):
    SIGNUP_OTP = "signup_otp"
    FORGOT_PASSWORD_OTP = "forgot_password_otp"
    ORDER_CONFIRMATION = "order_confirmation"
    GENERAL = "general"


class BaseNotificationProvider(ABC):
    """Abstract base class for all notification providers (email, sms, push, etc.)."""

    @abstractmethod
    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """Sends a notification to a specific recipient."""
        pass


class BaseEmailProvider(BaseNotificationProvider):
    """Abstract base class for email delivery providers."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        recipient_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Sends an email message with HTML and optional plain-text body."""
        pass

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        html_content = kwargs.get("html_content", message)
        recipient_name = kwargs.get("recipient_name")
        return await self.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html_content,
            text_content=message,
            recipient_name=recipient_name,
        )


class BaseSmsProvider(BaseNotificationProvider):
    """Abstract base class for SMS delivery providers (for future phone messaging extension)."""

    @abstractmethod
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> bool:
        """Sends an SMS message to a phone number."""
        pass

    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        return await self.send_sms(phone_number=recipient, message=message)
