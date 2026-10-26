import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from .schemas import (
    SignupRequest,
    LoginRequest,
    UpdateProfileRequest,
    VerifySignupOtpRequest,
    ResendOtpRequest,
    ForgotPasswordRequest,
    VerifyForgotPasswordOtpRequest,
    ResetPasswordRequest,
)
from .jwt import AuthHandler
from .otp import otpService, generate_otp
from rabbitmq.producer import rabbitProducer
from User.models import User, UserRole
from User.database import userRepository

logger = logging.getLogger(__name__)


def is_real_user(user: Optional[User]) -> bool:
    """Checks whether the user object corresponds to a registered customer rather than an auto-created guest."""
    if not user or not user.id:
        return False
    email = str(user.email or "").strip().lower()
    name = str(user.name or "").strip().lower()
    if email.endswith("@dukaan.local") or email.startswith("guest_") or name.startswith("guest "):
        return False
    return True


class AuthController:

    # =========================================================================
    # SIGNUP & EMAIL VERIFICATION OTP
    # =========================================================================

    async def request_signup_otp(self, payload: SignupRequest) -> Dict[str, Any]:
        """
        Validates signup input, creates a 6-digit verification code in Redis with
        5-minute TTL, and enqueues a notification to RabbitMQ for Brevo delivery.
        """
        clean_email = payload.email.strip().lower()
        existing = await userRepository.getUserByEmail(clean_email)
        if existing and is_real_user(existing):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account is already registered with this email. Please log in.",
            )

        # Generate 6-digit OTP
        otp_code = generate_otp(6)

        # Pre-hash password
        hashed_password = (
            AuthHandler.hash_password(payload.password)
            if payload.password
            else None
        )

        role_str = (
            payload.role.value
            if hasattr(payload.role, "value")
            else (payload.role or "customer")
        )

        extra_data = {
            "name": payload.name.strip(),
            "password_hash": hashed_password,
            "role": role_str,
            "address": payload.address,
            "thread_id": payload.thread_id,
        }

        # Store in Redis with 5-minute (300 seconds) TTL
        stored = otpService.store_otp(
            purpose="signup",
            identifier=clean_email,
            otp=otp_code,
            extra_data=extra_data,
            ttl_seconds=300,
        )

        if not stored:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize verification session. Please try again.",
            )

        # Enqueue email task to RabbitMQ producer
        await rabbitProducer.publish_notification(
            event_type="signup_otp",
            recipient=clean_email,
            data={
                "otp": otp_code,
                "name": payload.name,
                "ttl_minutes": 5,
            },
        )

        return {
            "success": True,
            "message": "A 6-digit verification code has been sent to your email. Valid for 5 minutes.",
            "email": clean_email,
        }

    async def verify_signup_otp(self, payload: VerifySignupOtpRequest):
        """
        Validates 6-digit OTP from Redis. If valid, completes registration in the database,
        issues JWT access token, and returns user session.
        """
        clean_email = payload.email.strip().lower()
        is_valid, error_msg, extra_data = otpService.verify_otp(
            purpose="signup",
            identifier=clean_email,
            entered_otp=payload.otp,
            delete_on_success=True,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        extra = extra_data or {}
        name = extra.get("name") or "Customer"
        hashed = extra.get("password_hash")
        role_raw = extra.get("role", "customer")
        role_enum = UserRole.MERCHANT if str(role_raw).lower() == "merchant" else UserRole.CUSTOMER
        address = extra.get("address")
        thread_id = extra.get("thread_id")

        # Check if user was already created
        existing = await userRepository.getUserByEmail(clean_email)
        if existing and is_real_user(existing):
            user_profile = existing
        else:
            new_user = User(
                name=name,
                password_hash=hashed,
                role=role_enum,
                email=clean_email,
                address=address,
            )
            user_profile = await userRepository.create(new_user)

        token = AuthHandler.create_access_token(
            user_profile.id,
            user_profile.role.value if hasattr(user_profile.role, "value") else str(user_profile.role),
        )

        if thread_id:
            try:
                from agents.user.controller import agentController
                asyncio.create_task(
                    agentController.sync_auth_state(
                        thread_id=thread_id,
                        user_id=user_profile.id,
                        token=token,
                    )
                )
            except Exception as e:
                logger.warning("Could not sync agent state on signup: %s", e)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "access_token": token,
                "user_id": user_profile.id,
                "role": user_profile.role.value if hasattr(user_profile.role, "value") else str(user_profile.role),
                "name": user_profile.name,
                "email": user_profile.email,
                "address": user_profile.address,
            },
        )

    async def resend_signup_otp(self, payload: ResendOtpRequest) -> Dict[str, Any]:
        """
        Regenerates a fresh 6-digit verification code with 5-minute TTL and resends it.
        """
        clean_email = payload.email.strip().lower()
        existing_info = otpService.get_otp_info("signup", clean_email)

        if not existing_info:
            existing_user = await userRepository.getUserByEmail(clean_email)
            if existing_user and is_real_user(existing_user):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This account is already registered. Please log in directly.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending signup session found. Please enter your registration details first.",
            )

        new_otp = generate_otp(6)
        extra_data = existing_info.get("extra_data", {})
        customer_name = extra_data.get("name", "Customer")

        otpService.store_otp(
            purpose="signup",
            identifier=clean_email,
            otp=new_otp,
            extra_data=extra_data,
            ttl_seconds=300,
        )

        await rabbitProducer.publish_notification(
            event_type="signup_otp",
            recipient=clean_email,
            data={
                "otp": new_otp,
                "name": customer_name,
                "ttl_minutes": 5,
            },
        )

        return {
            "success": True,
            "message": "A fresh 6-digit verification code has been dispatched to your email.",
            "email": clean_email,
        }

    # =========================================================================
    # FORGOT PASSWORD & RESET OTP
    # =========================================================================

    async def request_forgot_password_otp(self, payload: ForgotPasswordRequest) -> Dict[str, Any]:
        """
        Initiates password reset workflow: checks registered user, generates 6-digit OTP,
        saves to Redis with 5-minute TTL, and enqueues password reset email to RabbitMQ.
        """
        clean_email = payload.email.strip().lower()
        user = await userRepository.getUserByEmail(clean_email)

        if not user or not is_real_user(user):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No registered Dukaan account found with this email address.",
            )

        otp_code = generate_otp(6)
        otpService.store_otp(
            purpose="forgot_password",
            identifier=clean_email,
            otp=otp_code,
            extra_data={"user_id": user.id, "email": clean_email},
            ttl_seconds=300,
        )

        await rabbitProducer.publish_notification(
            event_type="forgot_password_otp",
            recipient=clean_email,
            data={
                "otp": otp_code,
                "name": user.name,
                "ttl_minutes": 5,
            },
        )

        return {
            "success": True,
            "message": "A 6-digit password reset code has been sent to your email.",
            "email": clean_email,
        }

    async def verify_forgot_password_otp(self, payload: VerifyForgotPasswordOtpRequest) -> Dict[str, Any]:
        """
        Verifies 6-digit OTP for password reset and issues a 10-minute reset authorization token.
        """
        clean_email = payload.email.strip().lower()
        is_valid, error_msg, _ = otpService.verify_otp(
            purpose="forgot_password",
            identifier=clean_email,
            entered_otp=payload.otp,
            delete_on_success=True,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        reset_token = otpService.store_reset_authorization(clean_email, ttl_seconds=600)

        return {
            "success": True,
            "message": "Verification code accepted. Please set your new password.",
            "reset_token": reset_token,
            "email": clean_email,
        }

    async def reset_password(self, payload: ResetPasswordRequest) -> Dict[str, Any]:
        """
        Resets user password after verifying either reset authorization token or fresh OTP.
        """
        clean_email = payload.email.strip().lower()

        # Validate authorization
        authorized = False
        if payload.reset_token:
            authorized = otpService.verify_reset_authorization(clean_email, payload.reset_token)
        elif payload.otp:
            is_valid, _, _ = otpService.verify_otp(
                purpose="forgot_password",
                identifier=clean_email,
                entered_otp=payload.otp,
                delete_on_success=True,
            )
            authorized = is_valid

        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset session has expired or is unauthorized. Please request a new code.",
            )

        if not payload.new_password or len(payload.new_password.strip()) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long.",
            )

        user = await userRepository.getUserByEmail(clean_email)
        if not user or not is_real_user(user):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found.",
            )

        new_hash = AuthHandler.hash_password(payload.new_password.strip())
        await userRepository.update_password(user.id, new_hash)

        if payload.reset_token:
            otpService.invalidate_reset_authorization(clean_email)

        return {
            "success": True,
            "message": "Your password has been successfully updated. Please log in with your new credentials.",
        }

    # =========================================================================
    # EXISTING COMPATIBILITY METHODS
    # =========================================================================

    async def signup(self, payload: SignupRequest):
        """
        Direct signup method for backwards compatibility with tests / API callers.
        """
        existing = await userRepository.getUserByEmail(payload.email)

        if existing and is_real_user(existing):
            raise HTTPException(
                status_code=409,
                detail="Your profile already exists. Please log in.",
            )

        hashed = (
            AuthHandler.hash_password(payload.password)
            if payload.password
            else None
        )

        user = User(
            name=payload.name,
            password_hash=hashed,
            role=payload.role or UserRole.CUSTOMER,
            email=payload.email,
            address=payload.address,
        )

        userProfile = await userRepository.create(user)

        token = AuthHandler.create_access_token(
            userProfile.id,
            userProfile.role.value if hasattr(userProfile.role, "value") else str(userProfile.role),
        )

        if payload.thread_id:
            try:
                from agents.user.controller import agentController
                asyncio.create_task(
                    agentController.sync_auth_state(
                        thread_id=payload.thread_id,
                        user_id=userProfile.id,
                        token=token,
                    )
                )
            except Exception as e:
                logger.warning("Could not sync agent state on signup: %s", e)

        return JSONResponse(
            status_code=201,
            content={
                "access_token": token,
                "user_id": userProfile.id,
                "role": userProfile.role.value if hasattr(userProfile.role, "value") else str(userProfile.role),
                "name": userProfile.name,
                "email": userProfile.email,
                "address": userProfile.address,
            },
        )

    async def login(self, payload: LoginRequest):
        user = await userRepository.getUserByEmail(payload.email)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Wrong credentials",
            )

        if not user.password_hash or not AuthHandler.verify_password(
            payload.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Wrong credentials",
            )

        token = AuthHandler.create_access_token(
            user.id,
            user.role.value if hasattr(user.role, "value") else str(user.role),
        )

        if payload.thread_id:
            try:
                from agents.user.controller import agentController
                asyncio.create_task(
                    agentController.sync_auth_state(
                        thread_id=payload.thread_id,
                        user_id=user.id,
                        token=token,
                    )
                )
            except Exception as e:
                logger.warning("Could not sync agent state on login: %s", e)

        return {
            "access_token": token,
            "user_id": user.id,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "name": user.name,
            "email": user.email,
            "address": user.address,
        }

    async def get_profile(self, user_id: int) -> Dict[str, Any]:
        user = await userRepository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found",
            )

        authenticated = is_real_user(user)
        return {
            "success": True,
            "user_id": user.id,
            "name": user.name,
            "email": user.email if authenticated else None,
            "address": user.address,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "is_authenticated": authenticated,
            "is_complete": bool(user.name and user.email and user.address and authenticated),
            "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        }

    async def update_profile(self, user_id: int, payload: UpdateProfileRequest) -> Dict[str, Any]:
        user = await userRepository.update_profile(
            user_id=user_id,
            name=payload.name,
            email=payload.email,
            address=payload.address,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found",
            )

        return {
            "success": True,
            "message": "Profile updated successfully",
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "address": user.address,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }

    async def check_status(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        if not user_id or user_id <= 0:
            return {
                "is_authenticated": False,
                "user_id": None,
                "role": "guest",
                "login_url": "/login",
                "signup_url": "/signup",
                "message": "Guest browsing session",
            }

        user = await userRepository.get_by_id(user_id)
        if not user or not is_real_user(user):
            return {
                "is_authenticated": False,
                "user_id": user_id,
                "role": "guest",
                "login_url": "/login",
                "signup_url": "/signup",
                "message": "Guest shopper. Please log in or sign up to save your cart and access exclusive discounts.",
            }

        return {
            "is_authenticated": True,
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "address": user.address,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "message": f"Welcome back, {user.name}!",
        }


authController = AuthController()
