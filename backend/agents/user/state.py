from typing import TypedDict, Annotated, Sequence, Optional, List, Any
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: int
    thread_id: str
    intent: Optional[str]
    gender: Optional[str]

    # Customer Identity, Profile & Authentication
    customer_profile: Optional[dict]
    is_authenticated: Optional[bool]
    auth_token: Optional[str]

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
    negotiated_products: Optional[dict]  # product_id (str) -> {product_id, product_name, discount_percentage, discounted_price, original_price}
    negotiation_log: Optional[List[dict]]  # Full audit history of each bargaining round
    cart_global_discount_percent: Optional[float]  # Combined discount on top of cart
    last_negotiated_product_id: Optional[int]

    # Payments & Checkout
    pending_payment_link: Optional[str]
    pending_payment_link_id: Optional[str]
    payment_confirmed: Optional[bool]

    # Order Placement & Tracking
    order_ids: Optional[List[int]]
    order_placed: Optional[bool]

    # UI Cards for Frontend Generative UI
    cards: Optional[List[dict]]

    # Memory & Summarization
    conversation_summary: Optional[str]
    important_facts: Optional[Any]
    last_seq: Optional[int]
    summarized_upto_seq: Optional[int]

    # Final Response Output
    final_response: str
