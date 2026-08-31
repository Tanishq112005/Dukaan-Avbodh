from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class A2AStartSessionResponse(BaseModel):
    chat_token: str = Field(..., description="Use this token in all subsequent interactions to maintain session state.")
    message: str = Field(..., description="Welcome message or instructions.")

class A2AInteractRequest(BaseModel):
    chat_token: str = Field(..., description="The session token received from /a2a/start_session")
    intent: str = Field(..., description="What the buyer agent wants to do (e.g., 'search for jeans', 'add product 1 to cart', 'negotiate 10% discount')")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured data like sizes, product IDs, etc.")

class A2AInteractResponse(BaseModel):
    status: str = Field(..., description="success, error, or counter_offer")
    message: str = Field(..., description="The response message from the Dukaan agent")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Any structured data returned (e.g., order details, cart contents, product lists)")
