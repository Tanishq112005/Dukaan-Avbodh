import sys
from .base import (
    NotificationChannel,
    NotificationType,
    BaseNotificationProvider,
    BaseEmailProvider,
    BaseSmsProvider,
)
from .service import NotificationService, notificationService, notification_service
from .providers.brevo import BrevoEmailProvider
from .templates import (
    render_signup_otp_email,
    render_forgot_password_otp_email,
    render_order_confirmation_email,
)

# Alias sys.modules for case-insensitive import compatibility
if "notification" not in sys.modules:
    sys.modules["notification"] = sys.modules[__name__]

__all__ = [
    "NotificationChannel",
    "NotificationType",
    "BaseNotificationProvider",
    "BaseEmailProvider",
    "BaseSmsProvider",
    "NotificationService",
    "notificationService",
    "notification_service",
    "BrevoEmailProvider",
    "render_signup_otp_email",
    "render_forgot_password_otp_email",
    "render_order_confirmation_email",
]
