# schemas/auth_schemas.py
from pydantic import BaseModel
from models.user import UserRole


class SignupRequest(BaseModel):
    name: str
    identifier: str          # email ya AI agent ID
    password: str | None = None
    role: UserRole = UserRole.CUSTOMER
    address: str | None = None


class LoginRequest(BaseModel):
    identifier: str
    password: str