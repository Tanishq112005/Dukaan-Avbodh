from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .order import Order

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    agent_type: str = "human"   # "human" ya "ai_agent" — track karne ke liye ki yeh real customer hai ya koi AI buyer-agent
    identifier: str = Field(unique=True)   # jaise email, ya AI agent ka unique ID/key
    created_at: datetime = Field(default_factory=datetime.utcnow)

    orders: List["Order"] = Relationship(back_populates="user")