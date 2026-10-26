import json
import time
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from config.redis import redisClient

logger = logging.getLogger(__name__)

DEFAULT_OTP_TTL_SECONDS = 300  # 5 minutes
MAX_VERIFICATION_ATTEMPTS = 5


def generate_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP string of specified length (default 6 digits)."""
    if length <= 0:
        length = 6
    min_val = 10 ** (length - 1)
    max_val = (10 ** length) - 1
    # secrets.randbelow is cryptographically secure
    code = secrets.randbelow(max_val - min_val + 1) + min_val
    return str(code)


class OTPService:
    """
    Manages OTP generation, storage with 5-minute TTL, attempt rate limiting,
    and single-use validation using Redis.
    """

    def __init__(self, redis_instance=None):
        self.redis_instance = redis_instance or redisClient

    def _get_client(self):
        return self.redis_instance.get_redis_client()

    def _format_key(self, purpose: str, identifier: str) -> str:
        clean_id = str(identifier or "").strip().lower()
        clean_purpose = str(purpose or "general").strip().lower()
        return f"otp:{clean_purpose}:{clean_id}"

    def store_otp(
        self,
        purpose: str,
        identifier: str,
        otp: str,
        extra_data: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = DEFAULT_OTP_TTL_SECONDS,
    ) -> bool:
        """
        Stores 6-digit OTP in Redis with specified TTL (default: 300 seconds / 5 minutes).
        """
        client = self._get_client()
        key = self._format_key(purpose, identifier)

        payload = {
            "otp": str(otp).strip(),
            "attempts": 0,
            "created_at": time.time(),
            "expires_at": time.time() + ttl_seconds,
            "extra_data": extra_data or {},
        }

        try:
            client.setex(key, ttl_seconds, json.dumps(payload))
            logger.info("[OTPService] Stored OTP for [%s] with TTL %ds", key, ttl_seconds)
            return True
        except Exception as e:
            logger.error("[OTPService] Failed to store OTP in Redis for %s: %s", key, e)
            return False

    def get_otp_info(self, purpose: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw OTP metadata from Redis without consuming it."""
        client = self._get_client()
        key = self._format_key(purpose, identifier)
        try:
            val = client.get(key)
            if not val:
                return None
            return json.loads(val.decode("utf-8") if isinstance(val, bytes) else val)
        except Exception as e:
            logger.error("[OTPService] Error fetching OTP info for %s: %s", key, e)
            return None

    def verify_otp(
        self,
        purpose: str,
        identifier: str,
        entered_otp: str,
        max_attempts: int = MAX_VERIFICATION_ATTEMPTS,
        delete_on_success: bool = True,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies entered OTP against stored Redis record.
        Enforces maximum attempt rate limit to prevent brute force.
        Deletes key upon successful verification (single-use).

        Returns: (is_valid, message, extra_data)
        """
        client = self._get_client()
        key = self._format_key(purpose, identifier)

        try:
            val = client.get(key)
            if not val:
                return False, "OTP has expired or does not exist. Please request a new verification code.", None

            data = json.loads(val.decode("utf-8") if isinstance(val, bytes) else val)
            stored_otp = str(data.get("otp", "")).strip()
            attempts = int(data.get("attempts", 0))

            if attempts >= max_attempts:
                # Exceeded maximum attempts - purge key to lock out further guesses
                client.delete(key)
                return False, "Maximum verification attempts exceeded. Please request a new OTP.", None

            clean_entered = str(entered_otp or "").strip()
            if not clean_entered or clean_entered != stored_otp:
                # Increment failed attempts count and update TTL remaining
                data["attempts"] = attempts + 1
                ttl_remaining = client.ttl(key)
                if ttl_remaining > 0:
                    client.setex(key, ttl_remaining, json.dumps(data))
                remaining = max(0, max_attempts - (attempts + 1))
                return False, f"Incorrect verification code. You have {remaining} attempts remaining.", None

            # OTP is valid!
            extra = data.get("extra_data") or {}
            if delete_on_success:
                client.delete(key)
                logger.info("[OTPService] OTP successfully verified and invalidated for [%s]", key)

            return True, "Verification successful.", extra

        except Exception as e:
            logger.exception("[OTPService] Verification exception for %s: %s", key, e)
            return False, f"Verification failed due to internal error: {str(e)}", None

    def store_reset_authorization(
        self,
        email: str,
        ttl_seconds: int = 600,
    ) -> str:
        """
        Creates a temporary reset authorization token in Redis (10 minutes)
        after successful forgot-password OTP verification.
        """
        client = self._get_client()
        clean_email = str(email).strip().lower()
        token = secrets.token_urlsafe(32)
        key = f"auth:reset_token:{clean_email}"
        try:
            client.setex(key, ttl_seconds, token)
            return token
        except Exception as e:
            logger.error("[OTPService] Failed storing reset authorization: %s", e)
            return token

    def verify_reset_authorization(self, email: str, token: str) -> bool:
        """Validates that user has verified their OTP and is authorized to set new password."""
        client = self._get_client()
        clean_email = str(email).strip().lower()
        key = f"auth:reset_token:{clean_email}"
        try:
            val = client.get(key)
            if not val:
                return False
            stored = val.decode("utf-8") if isinstance(val, bytes) else str(val)
            return stored == token
        except Exception as e:
            logger.error("[OTPService] Error checking reset token: %s", e)
            return False

    def invalidate_reset_authorization(self, email: str):
        """Purges reset authorization after password has been changed."""
        client = self._get_client()
        clean_email = str(email).strip().lower()
        key = f"auth:reset_token:{clean_email}"
        try:
            client.delete(key)
        except Exception:
            pass


# Singleton instance
otpService = OTPService()
otp_service = otpService
