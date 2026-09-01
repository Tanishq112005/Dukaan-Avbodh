# models/user_event.py — poora file
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    VIEWED = "viewed"
    PURCHASED = "purchased"
    SUGGESTION_ACCEPTED = "suggestion_accepted"
    SUGGESTION_SKIPPED = "suggestion_skipped"
    SESSION_START = "session_start"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"


class UserEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    product_id: Optional[int] = Field(default=None, foreign_key="product.id")   # Optional — session events ke liye product nahi hota
    event_type: EventType
    category: str = "session"                        # session events ke liye default "session"
    timestamp: datetime = Field(default_factory=datetime.utcnow)