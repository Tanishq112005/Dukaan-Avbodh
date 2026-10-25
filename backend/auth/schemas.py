# auth/schemas.py
from pydantic import BaseModel
from User.models import UserRole


class SignupRequest(BaseModel):
    name: str
    password: str | None = None
    email: str 
    role: UserRole | None = None


class LoginRequest(BaseModel):
    email: str 
    password: str
