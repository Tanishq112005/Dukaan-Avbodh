# models/user.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .order import Order


class UserRole(str, Enum):
    MERCHANT = "merchant"
    CUSTOMER = "customer"
    AI_AGENT = "ai_agent"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: UserRole = UserRole.CUSTOMER      # kaun hai — merchant/customer/ai_agent
    identifier: str = Field(unique=True)     # email ya AI agent ID
    password_hash: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    orders: List["Order"] = Relationship(back_populates="user")