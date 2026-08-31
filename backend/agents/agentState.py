from typing import TypedDict, Annotated, Sequence, Optional, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: int
    current_discount_percent: float
    combo_offer: Optional[dict]
    suggested_products: List[dict]
    final_response: str