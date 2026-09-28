from typing import List, Optional
from langchain_core.messages import BaseMessage, SystemMessage

def build_prompt_with_summary(
    system_prompt: str,
    messages: List[BaseMessage],
    intent: str,
    conversation_summary: Optional[str] = None,
    last_recent_count: int = 2,
    last_intent_count: int = 3
) -> List[BaseMessage]:
    """
    Builds the final message list sent to the LLM:

        [SystemMessage(static instructions + summary block)] + [recent/intent-filtered messages]

    - `conversation_summary` (older, compressed context) is appended to the END of the
      system prompt text -- keeps the static instruction block byte-identical across
      calls/users, which is what makes prefix-caching possible on the provider side.
    - The CURRENT user message is NOT duplicated as separate text -- it's already the
      last message inside `filter_history_by_intent`'s output (last_recent_count window),
      kept as a proper message object so tool-call structure isn't flattened into text.
    """
    filtered_messages = filter_history_by_intent(
        messages, intent, last_recent_count=last_recent_count, last_intent_count=last_intent_count
    )

    full_system_prompt = system_prompt
    if conversation_summary:
        full_system_prompt += f"\n\n--- Summary of earlier conversation (for context; older messages are no longer shown verbatim) ---\n{conversation_summary}"

    return [SystemMessage(content=full_system_prompt)] + filtered_messages


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
