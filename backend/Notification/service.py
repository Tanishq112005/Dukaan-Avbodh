import logging
from typing import Optional, Dict, Any

from Notification.base import (
    NotificationChannel,
    NotificationType,
    BaseEmailProvider,
    BaseSmsProvider,
)
from Notification.providers.brevo import BrevoEmailProvider
from Notification.templates import (
    render_signup_otp_email,
    render_forgot_password_otp_email,
    render_order_confirmation_email,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized Notification Service.
    Supports email delivery (via Brevo) with architecture ready for SMS / phone channels.
    """

    def __init__(
        self,
        email_provider: Optional[BaseEmailProvider] = None,
        sms_provider: Optional[BaseSmsProvider] = None,
    ):
        self.email_provider = email_provider or BrevoEmailProvider()
        self.sms_provider = sms_provider

    def set_email_provider(self, provider: BaseEmailProvider):
        """Allows dynamic switching or mocking of email providers."""
        self.email_provider = provider

    def set_sms_provider(self, provider: BaseSmsProvider):
        """Register or switch SMS provider for phone notifications."""
        self.sms_provider = provider

    async def send_signup_otp(
        self,
        to_email: str,
        otp: str,
        name: Optional[str] = None,
        ttl_minutes: int = 5,
    ) -> bool:
        """Sends the 6-digit verification OTP email to a registering user."""
        subject, html_content, text_content = render_signup_otp_email(
            name=name or "",
            otp=otp,
            ttl_minutes=ttl_minutes,
        )
        return await self.email_provider.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_name=name,
            metadata={"type": "signup_otp"},
        )

    async def send_forgot_password_otp(
        self,
        to_email: str,
        otp: str,
        name: Optional[str] = None,
        ttl_minutes: int = 5,
    ) -> bool:
        """Sends the 6-digit password reset OTP email."""
        subject, html_content, text_content = render_forgot_password_otp_email(
            name=name or "",
            otp=otp,
            ttl_minutes=ttl_minutes,
        )
        return await self.email_provider.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_name=name,
            metadata={"type": "forgot_password_otp"},
        )

    async def send_order_confirmation(
        self,
        to_email: str,
        order_data: Dict[str, Any],
    ) -> bool:
        """Sends the order receipt slip confirmation email."""
        subject, html_content, text_content = render_order_confirmation_email(order_data)
        customer_name = order_data.get("customer_name") or order_data.get("name")
        return await self.email_provider.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_name=customer_name,
            metadata={"type": "order_confirmation", "order_id": str(order_data.get("order_id", ""))},
        )

    async def dispatch(self, payload: Dict[str, Any]) -> bool:
        """
        Generic dispatcher used by queue consumers / workers to process notification payloads.
        """
        event_type = payload.get("type") or payload.get("event_type")
        channel = payload.get("channel", NotificationChannel.EMAIL.value)
        recipient = payload.get("recipient") or payload.get("to_email") or payload.get("email")

        if not recipient:
            logger.warning("[NotificationService] Missing recipient in notification payload: %s", payload)
            return False

        if channel == NotificationChannel.EMAIL.value:
            if event_type == NotificationType.SIGNUP_OTP.value or event_type == "EMAIL_OTP_SIGNUP":
                return await self.send_signup_otp(
                    to_email=recipient,
                    otp=str(payload.get("otp")),
                    name=payload.get("name"),
                    ttl_minutes=int(payload.get("ttl_minutes", 5)),
                )
            elif event_type == NotificationType.FORGOT_PASSWORD_OTP.value or event_type == "EMAIL_OTP_FORGOT_PASSWORD":
                return await self.send_forgot_password_otp(
                    to_email=recipient,
                    otp=str(payload.get("otp")),
                    name=payload.get("name"),
                    ttl_minutes=int(payload.get("ttl_minutes", 5)),
                )
            elif event_type == NotificationType.ORDER_CONFIRMATION.value or event_type == "ORDER_CONFIRMED":
                order_data = payload.get("order_data") or payload
                return await self.send_order_confirmation(
                    to_email=recipient,
                    order_data=order_data,
                )
            else:
                # General email fallback
                subject = payload.get("subject", "Notification from Dukaan")
                html = payload.get("html_content") or payload.get("message", "")
                text = payload.get("text_content") or payload.get("message", "")
                return await self.email_provider.send_email(
                    to_email=recipient,
                    subject=subject,
                    html_content=html,
                    text_content=text,
                    recipient_name=payload.get("name"),
                )

        elif channel == NotificationChannel.SMS.value:
            if not self.sms_provider:
                logger.info("[NotificationService] SMS channel invoked but no SMS provider registered. Recipient: %s", recipient)
                return False
            return await self.sms_provider.send_sms(
                phone_number=recipient,
                message=payload.get("message", ""),
            )

        else:
            logger.warning("[NotificationService] Unsupported channel: %s", channel)
            return False


# Singleton instance
notificationService = NotificationService()
notification_service = notificationService
