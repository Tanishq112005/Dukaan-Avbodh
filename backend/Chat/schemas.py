from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    user_id: int
    text: str
    thread_id: Optional[str] = None
    cart: List[dict] = []


class EventRequest(BaseModel):
    user_id: int
    event: str
    thread_id: Optional[str] = None
    cart: List[dict] = []


class MerchantChatRequest(BaseModel):
    message: str
