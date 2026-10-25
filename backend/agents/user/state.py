from typing import TypedDict, Annotated, Sequence, Optional, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):

    user_id: int
    current_discount_percent: float
    suggested_products: List[dict]
    final_response: str
    thread_id : str
    intent: Optional[str]
    conversation_summary: Optional[str]
    last_seq: Optional[int]
    gender : str
    summarized_upto_seq: Optional[int]
    important_facts : Optional[str] 