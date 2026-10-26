from typing import TypedDict, Annotated, Sequence, Optional, List, Any
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: int
    thread_id: str
    intent: Optional[str]
    gender: Optional[str]

    # Product Discovery & Recommendations
    suggested_products: List[dict]

    # Shopping Bag / Cart State
    cart: Optional[List[dict]]
    cart_items: Optional[List[dict]]
    cart_total: Optional[float]
    cart_subtotal: Optional[float]
    cart_count: Optional[int]

    # Pricing & Bargaining
    current_discount_percent: float
    combo_offer: Optional[Any]

    # Payments & Checkout
    pending_payment_link: Optional[str]
    pending_payment_link_id: Optional[str]

    # UI Cards for Frontend Generative UI
    cards: Optional[List[dict]]

    # Memory & Summarization
    conversation_summary: Optional[str]
    important_facts: Optional[Any]
    last_seq: Optional[int]
    summarized_upto_seq: Optional[int]

    # Final Response Output
    final_response: str
