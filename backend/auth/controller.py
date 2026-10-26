import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from .schemas import SignupRequest, LoginRequest, UpdateProfileRequest
from .jwt import AuthHandler
from User.models import User
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

    ## SignUp Process
    async def signup(self, payload: SignupRequest):
        existing = await userRepository.getUserByEmail(payload.email)

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Your profile already exists. Please log in."
            )

        hashed = (
            AuthHandler.hash_password(payload.password)
            if payload.password
            else None
        )

        user = User(
            name=payload.name,
            password_hash=hashed,
            role=payload.role,
            email=payload.email
        )

        userProfile = await userRepository.create(user)

        token = AuthHandler.create_access_token(
            userProfile.id,
            userProfile.role.value
        )

        if payload.thread_id:
            try:
                from agents.user.controller import agentController
                asyncio.create_task(
                    agentController.sync_auth_state(
                        thread_id=payload.thread_id,
                        user_id=userProfile.id,
                        token=token
                    )
                )
            except Exception as e:
                logger.warning("Could not sync agent state on signup: %s", e)

        return JSONResponse(
            status_code=201,
            content={
                "access_token": token,
                "user_id": userProfile.id,
                "role": userProfile.role.value,
                "name": userProfile.name,
                "email": userProfile.email,
            }
        )

    ## Login Process
    async def login(self, payload: LoginRequest):
        user = await userRepository.getUserByEmail(payload.email)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Wrong credentials"
            )

        if not user.password_hash or not AuthHandler.verify_password(
            payload.password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Wrong credentials"
            )

        token = AuthHandler.create_access_token(
            user.id,
            user.role.value
        )

        if payload.thread_id:
            try:
                from agents.user.controller import agentController
                asyncio.create_task(
                    agentController.sync_auth_state(
                        thread_id=payload.thread_id,
                        user_id=user.id,
                        token=token
                    )
                )
            except Exception as e:
                logger.warning("Could not sync agent state on login: %s", e)

        return {
            "access_token": token,
            "user_id": user.id,
            "role": user.role.value,
            "name": user.name,
            "email": user.email,
            "address": user.address,
        }

    ## Get Profile
    async def get_profile(self, user_id: int) -> Dict[str, Any]:
        user = await userRepository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found"
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

    ## Update Profile
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
                detail="Customer profile not found"
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

    ## Check Auth Status
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
