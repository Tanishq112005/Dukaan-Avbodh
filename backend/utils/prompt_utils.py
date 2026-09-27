from typing import List
from langchain_core.messages import BaseMessage

def filter_history_by_intent(
    messages: List[BaseMessage], 
    intent: str, 
    last_recent_count: int = 2,
    last_intent_count: int = 3
) -> List[BaseMessage]:
    """
    Filters the message history to include:
    1. Up to 'last_intent_count' recent messages matching the specific 'intent'.
    2. The most recent 'last_recent_count' messages (for immediate context).
    """
    recent_messages = messages[-last_recent_count:] if last_recent_count > 0 else []
    recent_msg_ids = {id(msg) for msg in recent_messages}
    
    intent_messages = []
    if last_intent_count > 0:
        for msg in reversed(messages):
            if msg.additional_kwargs.get("intent") == intent:
                intent_messages.append(msg)
                if len(intent_messages) == last_intent_count:
                    break
                    
    intent_msg_ids = {id(msg) for msg in intent_messages}
    
    filtered = []
    for msg in messages:
        if id(msg) in recent_msg_ids or id(msg) in intent_msg_ids:
            filtered.append(msg)
            
    return filtered
