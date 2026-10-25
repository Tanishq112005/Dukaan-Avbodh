import re
import logging
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.user.state import AgentState
from utils.prompt_utils import filter_history_by_intent
from .interfaces import IAgentInterface

logger = logging.getLogger(__name__)


class Route(BaseModel):
    """Route the user's request to the appropriate specialist agent."""
    intent: Literal["recommendation", "cart", "negotiation", "general"] = Field(
        description=(
            "The specialized agent to route to: "
            "'recommendation' for searching, catalog browsing, or fashion recommendations, "
            "'cart' for adding/updating/removing items or checking cart summary, "
            "'negotiation' for discounts, combo offers, and price bargaining, "
            "'general' for greetings, casual chat, store FAQ, or discovering shopper preferences (men/women, category)."
        )
    )


class DirectorAgent(IAgentInterface):
    """
    Director / Router Agent.
    Analyzes the customer's request and routes to the appropriate specialist agent.
    Re-evaluates intent when tools return results to dynamically handle follow-up actions (e.g. adding to cart or negotiating).
    """

    def __init__(self, llm):
        self.intent = "director"
        self.system_prompt = """You are the intelligent intent classification router for Dukaan, a premium clothing and fashion e-commerce store.
Your job is to analyze the conversation history, user request, and any recent tool results to classify the NEXT action into EXACTLY ONE intent:

1. 'recommendation':
   - User wants to find, search, browse, or ask for clothing recommendations.
   - User mentions specific items, categories, colors, or styles (e.g., "show me blue jeans", "recommend some shirts", "what hoodies do you have?").
   - Products were just fetched by tools and the recommendation specialist needs to present them to the customer.

2. 'cart':
   - User wants to add, delete, update, or remove items in their shopping bag.
   - User mentions cart operations (e.g., "add this to cart", "remove the jeans", "change quantity to 2").
   - User asks to inspect or view cart contents, bag status, or total price summary (e.g., "what's in my cart?", "view my bag", "cart summary", "clear my cart").
   - If a product was just recommended and the user also asked to add it, route to 'cart'.

3. 'negotiation':
   - User asks for discounts, deals, combo offers, or better prices (e.g., "can I get a discount?", "can you do 10% off?", "what is your best price?", "give me a deal").
   - User is actively bargaining, negotiating, or asking for special offers.
   - User is accepting or declining combo offers or discount deals.
   - If an item was added and the user also asked for a discount, route to 'negotiation'.

4. 'general':
   - Greetings (e.g., "hello", "hi", "hey"), casual chat, goodbyes.
   - Initial vague shopping queries where the shopper's gender, occasion, or clothing interest is not yet known (e.g., "I need some clothes", "help me shop", "looking for an outfit").
   - The user needs assistance clarifying what they want before browsing products (e.g. asking whether they want men's or women's clothes).
   - General questions about store policies, shipping, returns, delivery, or general styling advice.

Analyze the request and context carefully and output the single best matching intent."""

        self.llm = llm.with_structured_output(Route)

    def _build_prompt(self, messages):
        cleaned = []
        for msg in messages:
            msg_type = getattr(msg, "type", "")
            if msg_type == "tool" or msg.__class__.__name__ == "ToolMessage":
                continue
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                content = getattr(msg, "content", "")
                if content:
                    cleaned.append(AIMessage(content=str(content)))
                continue
            cleaned.append(msg)

        filtered_messages = filter_history_by_intent(
            cleaned, self.intent, last_recent_count=6, last_intent_count=0
        )
        return [SystemMessage(content=self.system_prompt)] + filtered_messages

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

    def run(self, state: AgentState):
        messages = state.get("messages", [])
        prompt = self._build_prompt(messages)

        # Uses structured output to determine route; does not append to visible chat history
        try:
            route_obj = self.llm.invoke(prompt)
        except Exception as e:
            logger.warning("Director structured routing invoke failed: %s", e)
            route_obj = None

        intent = "general"
        if route_obj is not None:
            if hasattr(route_obj, "intent") and route_obj.intent:
                intent = str(route_obj.intent).lower()
            elif isinstance(route_obj, dict) and route_obj.get("intent"):
                intent = str(route_obj["intent"]).lower()

        if intent not in ["recommendation", "cart", "negotiation", "general"]:
            # Fallback heuristic from user message content
            last_human_text = ""
            for m in reversed(messages):
                if getattr(m, "type", "") == "human" or m.__class__.__name__ == "HumanMessage":
                    last_human_text = str(getattr(m, "content", "")).lower()
                    break

            if any(w in last_human_text for w in ["cart", "bag", "remove", "quantity", "checkout"]):
                intent = "cart"
            elif any(w in last_human_text for w in ["discount", "bargain", "cheaper", "offer", "price", "deal"]):
                intent = "negotiation"
            elif any(w in last_human_text for w in ["jeans", "shirt", "hoodie", "show", "find", "search", "looking for", "buy"]):
                intent = "recommendation"
            else:
                intent = "general"

        updates = {"intent": intent}

        # If gender is not yet set in state, detect if explicitly mentioned
        current_gender = state.get("gender")
        if not current_gender:
            detected = self._detect_gender(messages)
            if detected:
                updates["gender"] = detected

        return updates
