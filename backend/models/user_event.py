# models/user_event.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    VIEWED = "viewed"
    PURCHASED = "purchased"
    SUGGESTION_ACCEPTED = "suggestion_accepted"
    SUGGESTION_SKIPPED = "suggestion_skipped"
    # baad mein cart banega toh "added_to_cart" yahan add kar dena


class UserEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="product.id")
    event_type: EventType
    category: str                        # Product.type ki value — fast querying ke liye denormalized
    timestamp: datetime = Field(default_factory=datetime.utcnow)