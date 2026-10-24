# schemas/auth_schemas.py
from pydantic import BaseModel
from models.user import UserRole


class SignupRequest(BaseModel):
    name: str
    password: str | None = None
    email : str 
    role: UserRole | None 


class LoginRequest(BaseModel):
    email : str 
    password: str