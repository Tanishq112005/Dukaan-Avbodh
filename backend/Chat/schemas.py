from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    user_id: int
    text: str
    thread_id: Optional[str] = None
    cart: List[dict] = []
    access_token: Optional[str] = None


class EventRequest(BaseModel):
    user_id: int
    event: str
    thread_id: Optional[str] = None
    cart: List[dict] = []
    access_token: Optional[str] = None


class AuthSyncRequest(BaseModel):
    thread_id: Optional[str] = None
    access_token: Optional[str] = None
    user_id: Optional[int] = None
    event: Optional[str] = "login"


class MerchantChatRequest(BaseModel):
    message: str


class CreateThreadRequest(BaseModel):
    user_id: int
    thread_id: str


class AddMessageRequest(BaseModel):
    user_id: int
    sender: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateStatePatchRequest(BaseModel):
    user_id: int
    patch: Dict[str, Any]


class AppendNegotiationLogRequest(BaseModel):
    user_id: int
    log: Dict[str, Any]
