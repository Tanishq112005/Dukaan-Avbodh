from fastapi import APIRouter, Depends, Query, status
from typing import Optional

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
from .controller import authController
from middleware.auth_middleware import auth_middleware

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------------------------------------------------------
# Signup & Email Verification Endpoints
# -----------------------------------------------------------------------------

@router.post("/signup/request-otp", status_code=status.HTTP_200_OK)
async def request_signup_otp(payload: SignupRequest):
    """Generates and sends 6-digit email verification OTP for signup (5 min TTL)."""
    return await authController.request_signup_otp(payload)


@router.post("/signup/verify-otp", status_code=status.HTTP_201_CREATED)
async def verify_signup_otp(payload: VerifySignupOtpRequest):
    """Verifies signup OTP from Redis and activates user account."""
    return await authController.verify_signup_otp(payload)


@router.post("/signup/resend-otp", status_code=status.HTTP_200_OK)
async def resend_signup_otp(payload: ResendOtpRequest):
    """Resends a new 6-digit verification code with fresh 5-minute TTL."""
    return await authController.resend_signup_otp(payload)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest):
    """Direct signup endpoint (backward compatible)."""
    return await authController.signup(payload)


# -----------------------------------------------------------------------------
# Forgot Password & Reset Endpoints
# -----------------------------------------------------------------------------

@router.post("/forgot-password/request-otp", status_code=status.HTTP_200_OK)
async def request_forgot_password_otp(payload: ForgotPasswordRequest):
    """Initiates password reset by sending 6-digit OTP to user email (5 min TTL)."""
    return await authController.request_forgot_password_otp(payload)


@router.post("/forgot-password/verify-otp", status_code=status.HTTP_200_OK)
async def verify_forgot_password_otp(payload: VerifyForgotPasswordOtpRequest):
    """Validates password reset OTP from Redis and issues reset token."""
    return await authController.verify_forgot_password_otp(payload)


@router.post("/forgot-password/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest):
    """Updates account password after OTP / reset authorization token verification."""
    return await authController.reset_password(payload)


# -----------------------------------------------------------------------------
# Login & Profile Endpoints
# -----------------------------------------------------------------------------

@router.post("/login")
async def login(payload: LoginRequest):
    return await authController.login(payload)


@router.get("/me")
@router.get("/profile")
async def get_my_profile(current_user: dict = Depends(auth_middleware)):
    return await authController.get_profile(current_user["user_id"])


@router.put("/profile")
async def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: dict = Depends(auth_middleware),
):
    return await authController.update_profile(current_user["user_id"], payload)


@router.get("/status")
async def check_status(user_id: Optional[int] = Query(None)):
    return await authController.check_status(user_id)
