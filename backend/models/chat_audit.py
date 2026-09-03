from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime

class ChatMessage(BaseModel):
    sender: Literal["human", "ai", "system"]
    message: str
    tool_calls: Optional[List[Dict[str, Any]]] = None  # To show audit (what action, why)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AppliedCampaignSnapshot(BaseModel):
    campaign_id: int
    agenda: str = ""
    discount_percentage: float = 0.0
    type: Optional[str] = None
    priority: int = 0

class NegotiationLog(BaseModel):
    requested: float
    agent_offered: float
    accepted: bool
    counter_offer_price: Optional[float] = None
    margin: Optional[float] = None
    loss_leader: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ThreadState(BaseModel):
    current_discount_percent: float = 0.0
    suggested_products: List[Any] = []
    combo_offer: Optional[Dict[str, Any]] = None
    kit_products: List[Dict[str, Any]] = []
    ordered_products: List[Dict[str, Any]] = []
    
    # New fields for merchant dashboard visualization
    negotiation_log: List[NegotiationLog] = []
    cart_products: List[Dict[str, Any]] = []
    max_discount_we_can_give: float = 0.0
    total_cost_price: float = 0.0
    total_selling_price: float = 0.0
    new_selling_price_total: float = 0.0
    combo_margin: float = 0.0
    applied_campaigns: List[AppliedCampaignSnapshot] = []
    campaign_priced_products: List[Dict[str, Any]] = []
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
