from typing import List, Optional, Any
import json
from langchain_core.messages import BaseMessage, SystemMessage


def format_important_facts(facts: Any) -> Optional[str]:
    """
    Formats customer memory facts (gender, budget, known sizes, emotions/reasons)
    into a structured, human-readable context block for specialist prompts.
    """
    if not facts:
        return None
    if isinstance(facts, str):
        clean = facts.strip()
        return clean if clean else None
    if isinstance(facts, dict):
        lines = []
        gender = facts.get("gender")
        if gender:
            lines.append(f"- Gender Preference: {gender}")
        budget = facts.get("budget")
        if isinstance(budget, dict):
            min_b = budget.get("min_budget")
            max_b = budget.get("max_budget")
            if min_b is not None or max_b is not None:
                lines.append(f"- Budget Range: Min {min_b or 0}, Max {max_b or 'No limit'}")
        emotion = facts.get("emotion")
        if emotion and isinstance(emotion, list):
            lines.append(f"- Occasion / Shopping Reason: {', '.join(str(e) for e in emotion)}")
        size = facts.get("size")
        if isinstance(size, dict):
            size_strs = [f"{k}: {v}" for k, v in size.items() if v]
            if size_strs:
                lines.append(f"- Known Apparel Sizes: {', '.join(size_strs)}")
        if not lines:
            try:
                return json.dumps(facts)
            except Exception:
                return str(facts)
        return "\n".join(lines)
    return str(facts)


def build_prompt_with_summary(
    system_prompt: str,
    messages: List[BaseMessage],
    intent: str,
    conversation_summary: Optional[str] = None,
    important_facts: Optional[Any] = None,
    last_recent_count: int = 2,
    last_intent_count: int = 3
) -> List[BaseMessage]:
    """
    Builds the final message list sent to the LLM:

        [SystemMessage(static instructions + important facts + summary block)] + [recent/intent-filtered messages]

    - `important_facts` (persisted customer profile, sizes, budget, occasion) is injected
      to ground the agent without repeatedly asking the user for already-known info.
    - `conversation_summary` (older, compressed context) is appended to the END of the
      system prompt text -- keeps the static instruction block byte-identical across
      calls/users, preserving prefix-caching benefits.
    - The CURRENT user message is kept in the filtered history window as a proper message object.
    """
    filtered_messages = filter_history_by_intent(
        messages, intent, last_recent_count=last_recent_count, last_intent_count=last_intent_count
    )

    full_system_prompt = system_prompt

    formatted_facts = format_important_facts(important_facts)
    if formatted_facts:
        full_system_prompt += (
            f"\n\n--- Customer Known Facts & Preferences ---\n"
            f"{formatted_facts}\n"
            f"(Utilize these known customer preferences, sizes, budget, and reasons to provide accurate, personalized recommendations and avoid re-asking for information already provided.)"
        )

    if conversation_summary:
        full_system_prompt += f"\n\n--- Summary of earlier conversation (for context; older messages are no longer shown verbatim) ---\n{conversation_summary}"

    return [SystemMessage(content=full_system_prompt)] + filtered_messages


def filter_history_by_intent(
    messages: List[BaseMessage], 
    intent: str, 
    last_recent_count: int = 4,
    last_intent_count: int = 4
) -> List[BaseMessage]:
    """
    Filters the message history to include:
    1. All messages from the latest HumanMessage onwards (guarantees the active user question and subsequent tool calls are never dropped).
    2. Up to 'last_intent_count' recent messages matching the specific 'intent'.
    3. The most recent 'last_recent_count' messages for immediate conversational context.
    """
    if not messages:
        return []

    # 1. Always preserve the active user turn from the most recent HumanMessage
    latest_turn_ids = set()
    for idx in range(len(messages) - 1, -1, -1):
        latest_turn_ids.add(id(messages[idx]))
        if getattr(messages[idx], "type", None) == "human" or getattr(messages[idx], "role", None) == "user":
            break

    # 2. Most recent messages
    recent_messages = messages[-last_recent_count:] if last_recent_count > 0 else []
    recent_msg_ids = {id(msg) for msg in recent_messages}

    # 3. Intent-specific messages
    intent_messages = []
    if last_intent_count > 0:
        for msg in reversed(messages):
            if msg.additional_kwargs.get("intent") == intent:
                intent_messages.append(msg)
                if len(intent_messages) == last_intent_count:
                    break

    intent_msg_ids = {id(msg) for msg in intent_messages}

    # Preserve exact chronological order
    filtered = []
    for msg in messages:
        msg_id = id(msg)
        if msg_id in latest_turn_ids or msg_id in recent_msg_ids or msg_id in intent_msg_ids:
            has_tool_calls = bool(getattr(msg, "tool_calls", None))
            content = getattr(msg, "content", None)
            has_content = bool(content and str(content).strip())
            if not has_tool_calls and not has_content:
                continue
            filtered.append(msg)

    return filtered
