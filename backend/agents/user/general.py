import re
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from .interfaces import IAgentInterface


class GeneralAgent(IAgentInterface):
    """
    General Inquiry & Shopper Profile Discovery Agent.
    Welcomes customers, answers general questions, and actively collects
    style preferences (men vs women, clothing category, occasion, size, budget)
    to prime the recommendation engine.
    """

    def __init__(self, llm, tools=None):
        self.intent = "general"
        self.system_prompt = """You are the personal stylist Dukaan AI and friendly sales advisor for Dukaan, a premium clothing and fashion store.

Your primary mission is to welcome the customer, answer general inquiries, and actively discover their style preferences so our recommendation engine can find the perfect clothes for them.

### YOUR RESPONSIBILITIES:
1. GREETING & CASUAL CHAT:
   - Welcome the user warmly with a proactive, witty, and polite tone.
   - Introduce yourself as their Dukaan personal fashion stylist.

2. ACTIVE INFORMATION COLLECTION (Style Discovery):
   - Determine who they are shopping for: ALWAYS clarify whether they are looking for **Men's** or **Women's** clothing if not already known.
   - Inquire about their occasion or shopping reason (e.g. casual everyday wear, party, wedding, office/formal, vacation, workout, gift).
   - Inquire about their preferred clothing category (shirts, t-shirts, jeans, trousers, hoodies, jackets, dresses, etc.) or preferred style/color.
   - DO NOT ask for apparel sizes during discovery or general conversation! Sizes are only requested when the customer decides to add an item to their cart.
   - Keep it natural, conversational, and focused: ask 1 or 2 targeted questions at a time rather than overwhelming the customer.

3. CONTEXT & MEMORY AWARENESS:
   - Review Customer Known Facts and Conversation Summary below.
   - If their gender or budget are ALREADY known, do NOT re-ask! Use that knowledge to make your response personal and direct.

4. SEAMLESS HANDOFF:
   - Once the user shares who they are shopping for (men/women) and what they need, warmly acknowledge their choice and invite them to view our collection (the system will seamlessly route to the Recommendation Agent on their next message).

### CONSTRAINTS:
- English ONLY. NEVER output internal thought tags (<thought>, <think>), reasoning traces, or internal notes. Return ONLY your friendly, helpful customer-facing response.
- Do NOT invent fake products, stock codes, or specific SKU prices in this general mode."""

        self.tools = tools or []

        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _detect_gender(self, messages) -> Optional[str]:
        for msg in reversed(messages):
            msg_type = getattr(msg, "type", "")
            is_human = (msg_type == "human") or (msg.__class__.__name__ == "HumanMessage")
            if is_human:
                content = str(getattr(msg, "content", "")).lower()
                if re.search(r"\b(women|womens|women's|woman|female|ladies|girls?)\b", content):
                    return "women"
                if re.search(r"\b(men|mens|men's|man|male|gentlemen|guys?|boys?)\b", content):
                    return "men"
                if re.search(r"\b(unisex)\b", content):
                    return "unisex"
                break
        return None

    def _build_prompt(self, state: AgentState):
        messages = state.get("messages", [])
        conversation_summary = state.get("conversation_summary")
        important_facts = state.get("important_facts")
        return build_prompt_with_summary(
            self.system_prompt,
            messages,
            self.intent,
            conversation_summary=conversation_summary,
            important_facts=important_facts,
            last_recent_count=6,
            last_intent_count=0,
        )

    def run(self, state: AgentState):
        prompt = self._build_prompt(state)

        response = self.llm.invoke(prompt)
        if not (getattr(response, "content", None) and str(response.content).strip()):
            response.content = "Hello! Welcome to Dukaan. How can I help you style your look today?"
        response.additional_kwargs["intent"] = self.intent

        updates = {"messages": [response], "intent": self.intent}

        current_gender = state.get("gender")
        if not current_gender:
            detected = self._detect_gender(state.get("messages", []))
            if detected:
                updates["gender"] = detected

        return updates
