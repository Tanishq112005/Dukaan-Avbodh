from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatMessage(BaseModel):
    sender: Literal["human", "ai", "system"]
    message: str
    tool_calls: Optional[List[Dict[str, Any]]] = None  # To show audit (what action, why)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class NegotiationLog(BaseModel):
    requested: float
    agent_offered: float
    accepted: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ThreadState(BaseModel):
    current_discount_percent: float = 0.0
    suggested_products: List[Any] = []
    combo_offer: Optional[Dict[str, Any]] = None
    
    # New fields for merchant dashboard visualization
    negotiation_log: List[NegotiationLog] = []
    cart_products: List[Dict[str, Any]] = []
    max_discount_we_can_give: float = 0.0
    total_cost_price: float = 0.0
    total_selling_price: float = 0.0
    final_profit: float = 0.0
    
    order_placed: bool = False
    razorpay_id: Optional[str] = None
    payment_status: Optional[str] = None
    user_info: Optional[Dict[str, str]] = None
    
class ChatThread(BaseModel):
    user_id: int
    thread_id: str
    messages: List[ChatMessage] = []
    state: ThreadState = Field(default_factory=ThreadState)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
