# auth/schemas.py
from pydantic import BaseModel
from typing import Optional
from User.models import UserRole


class SignupRequest(BaseModel):
    name: str
    password: Optional[str] = None
    email: str 
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    email: str 
    password: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
