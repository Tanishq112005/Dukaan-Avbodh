from pydantic import BaseModel
from typing import Optional
from User.models import UserRole


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    address: Optional[str] = None
