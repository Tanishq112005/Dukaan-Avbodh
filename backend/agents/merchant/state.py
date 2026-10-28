from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict, total=False):
    """
    Rich, verifiable state schema for the Dukaan Merchant AI Agent.
    Tracks conversational history, tool executions, analytical snapshots,
    Generative UI cards, and business metrics for multi-turn merchant queries
    and transparent MongoDB audit persistence.
    """
    # 1. Conversational History & Session Identity
    messages: Annotated[Sequence[BaseMessage], operator.add]
    merchant_id: int
    user_id: int
    thread_id: str

    # 2. Intent and Tool Execution Audit
    intent: Optional[str]
    current_intent: Optional[str]
    last_tool_called: Optional[str]
    last_tool_args: Optional[Dict[str, Any]]
    last_tool_result: Optional[Dict[str, Any]]

    # 3. Business Context Caching (for coherent multi-turn reasoning)
    analytics_context: Optional[Dict[str, Any]]
    top_selling_products: Optional[List[Dict[str, Any]]]
    inventory_alerts: Optional[List[Dict[str, Any]]]
    order_lookup: Optional[Dict[str, Any]]
    negotiation_insights: Optional[Dict[str, Any]]
    pricing_updates: Optional[Dict[str, Any]]

    # 4. Generative UI Cards for Dashboard / Chat Interface
    cards: Optional[List[Dict[str, Any]]]

    # 5. Memory & Conversation Summarization
    conversation_summary: Optional[str]
    important_facts: Optional[Any]

    # 6. Agent Output & Error Tracking
    error: Optional[str]
    final_response: str
    metadata: Optional[Dict[str, Any]]
