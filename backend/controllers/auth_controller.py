# controllers/auth_controller.py
from fastapi import HTTPException
from schemas.auth_schemas import SignupRequest, LoginRequest
from repositories import UserRepository
from auth.auth_handler import AuthHandler
from models import User


class AuthController:
    def __init__(self):
        self.user_repo = UserRepository()

    async def signup(self, payload: SignupRequest):
        existing = await self.user_repo.get_by_identifier(payload.identifier)
        if existing:
            raise HTTPException(status_code=400, detail="Yeh identifier pehle se registered hai")

        hashed = AuthHandler.hash_password(payload.password) if payload.password else None
        user = User(
            name=payload.name,
            identifier=payload.identifier,
            password_hash=hashed,
            role=payload.role
        )
        created = await self.user_repo.create(user)
        token = AuthHandler.create_access_token(created.id, created.role.value)
        return {"access_token": token, "user_id": created.id, "role": created.role.value}

    async def login(self, payload: LoginRequest):
        user = await self.user_repo.get_by_identifier(payload.identifier)
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Galat credentials")

        if not AuthHandler.verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Galat credentials")

        token = AuthHandler.create_access_token(user.id, user.role.value)
        return {"access_token": token, "user_id": user.id, "role": user.role.value}