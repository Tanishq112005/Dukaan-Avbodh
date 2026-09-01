from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatMessage(BaseModel):
    sender: Literal["human", "ai", "system"]
    message: str
    tool_calls: Optional[List[Dict[str, Any]]] = None  # To show audit (what action, why)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ThreadState(BaseModel):
    current_discount_percent: float = 0.0
    suggested_products: List[Any] = []
    combo_offer: Optional[Dict[str, Any]] = None

class ChatThread(BaseModel):
    user_id: int
    thread_id: str
    messages: List[ChatMessage] = []
    state: ThreadState = Field(default_factory=ThreadState)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
