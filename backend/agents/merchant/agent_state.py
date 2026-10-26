from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    Rich, verifiable state schema for the Dukaan Merchant AI Agent.
    Tracks conversation history, tool executions, and analytical snapshots
    for multi-turn merchant queries and transparent MongoDB audit persistence.
    """
    # 1. Conversational History
    messages: Annotated[Sequence[BaseMessage], operator.add]
    merchant_id: int
    user_id: int
    thread_id: str

    # 2. Intent and Tool Execution Audit
    current_intent: Optional[str]
    last_tool_called: Optional[str]
    last_tool_args: Optional[Dict[str, Any]]
    last_tool_result: Optional[Dict[str, Any]]

    # 3. Business Context Caching (for coherent multi-turn reasoning)
    analytics_context: Optional[Dict[str, Any]]

    # 4. Agent Output & Error Tracking
    error: Optional[str]
    final_response: str
    metadata: Optional[Dict[str, Any]]
