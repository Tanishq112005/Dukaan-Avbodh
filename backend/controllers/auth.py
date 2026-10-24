
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from schemas.auth import SignupRequest, LoginRequest
from lib.jwt import AuthHandler
from models import User
from repositories.user import userRepository


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
            identifier=payload.identifier,
            password_hash=hashed,
            role=payload.role,
            email=payload.email
        )

        userProfile = await userRepository.get_or_create(user)

        token = AuthHandler.create_access_token(
            userProfile.id,
            userProfile.role.value
        )

        return JSONResponse(
            status_code=201,
            content={
                "access_token": token,
                "user_id": userProfile.id,
                "role": userProfile.role.value
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

        return {
            "access_token": token,
            "user_id": user.id,
            "role": user.role.value
        }


authController = AuthController()
