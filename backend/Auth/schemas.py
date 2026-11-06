# auth/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from User.models import UserRole


class SignupRequest(BaseModel):
    name: str
    password: Optional[str] = None
    email: str 
    role: Optional[UserRole] = None
    address: Optional[str] = None
    thread_id: Optional[str] = None


class VerifySignupOtpRequest(BaseModel):
    email: str
    otp: str


class ResendOtpRequest(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyForgotPasswordOtpRequest(BaseModel):
    email: str
    otp: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    reset_token: Optional[str] = None
    otp: Optional[str] = None


class LoginRequest(BaseModel):
    email: str 
    password: str
    thread_id: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class CreateAgentSessionRequest(BaseModel):
    agent_name: Optional[str] = "AI Shopping Assistant"
    scopes: Optional[List[str]] = None
    custom_base_url: Optional[str] = None
