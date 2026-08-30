from typing import TypedDict, Annotated, Sequence, Optional, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: int
    
    # Negotiation state
    current_discount_percent: float
    combo_offer: Optional[dict]
    
    # Recommendation/Search state
    suggested_products: List[dict]
    
    # The final text to send to the user via websocket
    final_response: str