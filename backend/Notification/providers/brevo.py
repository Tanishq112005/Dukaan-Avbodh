import os
import logging
from typing import Optional, Dict, Any
import httpx
from Notification.base import BaseEmailProvider

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailProvider(BaseEmailProvider):
    """
    Brevo (formerly Sendinblue) Transactional Email Provider.
    Sends emails via Brevo REST API v3 using HTTPS.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("BREVO_API_KEY") or os.getenv("SENDINBLUE_API_KEY", "")
        self.sender_email = (
            sender_email
            or os.getenv("BREVO_SENDER_EMAIL")
            or os.getenv("EMAIL_SENDER_ADDRESS")
            or "noreply@dukaan.com"
        )
        self.sender_name = (
            sender_name
            or os.getenv("BREVO_SENDER_NAME")
            or os.getenv("EMAIL_SENDER_NAME")
            or "Dukaan Store"
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        recipient_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Sends an email via Brevo REST API.
        If no API key is provided, falls back to simulated delivery (for local/testing).
        """
        if not to_email:
            logger.warning("[BrevoEmailProvider] Recipient email is missing.")
            return False

        # In case API key is not configured, simulate delivery safely
        if not self.api_key or self.api_key.strip() in ("", "dummy", "test", "your_brevo_api_key"):
            logger.info(
                "[BrevoEmailProvider: SIMULATED] Brevo API key not configured. "
                "Simulating email dispatch to <%s>. Subject: '%s'",
                to_email,
                subject,
            )
            return True

        headers = {
            "accept": "application/json",
            "api-key": self.api_key.strip(),
            "content-type": "application/json",
        }

        recipient_payload: Dict[str, Any] = {"email": to_email}
        if recipient_name:
            recipient_payload["name"] = recipient_name

        payload: Dict[str, Any] = {
            "sender": {
                "name": self.sender_name,
                "email": self.sender_email,
            },
            "to": [recipient_payload],
            "subject": subject,
            "htmlContent": html_content,
        }

        if text_content:
            payload["textContent"] = text_content

        if metadata:
            payload["tags"] = [str(k) for k in metadata.keys() if isinstance(k, str)]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(BREVO_API_URL, headers=headers, json=payload)

                if response.status_code in (200, 201, 202):
                    res_data = response.json()
                    message_id = res_data.get("messageId", "ok")
                    logger.info(
                        "[BrevoEmailProvider] Email successfully dispatched to %s. MessageID: %s",
                        to_email,
                        message_id,
                    )
                    return True
                else:
                    logger.error(
                        "[BrevoEmailProvider] Failed to send email to %s. Status %d: %s",
                        to_email,
                        response.status_code,
                        response.text,
                    )
                    return False
        except httpx.RequestError as exc:
            logger.error("[BrevoEmailProvider] HTTP Request error sending email to %s: %s", to_email, exc)
            return False
        except Exception as exc:
            logger.exception("[BrevoEmailProvider] Unexpected error sending email to %s: %s", to_email, exc)
            return False
