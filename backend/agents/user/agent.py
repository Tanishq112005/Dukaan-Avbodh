"""
Unified User Agent for Dukaan E-Commerce.
Replaces fragmented specialist agents (Director, Recommendation, Cart, Negotiation, General)
with a single, highly capable shopping stylist agent equipped with all catalog, cart, bargaining, order, and auth tools.
"""
import re
import asyncio
import logging
from typing import List, Optional, Any

from langchain_core.messages import BaseMessage
from agents.user.interfaces import IAgentInterface
from agents.user.state import AgentState
from agents.user.prompts import get_user_agent_prompt
from utils.prompt_utils import build_prompt_with_summary

logger = logging.getLogger(__name__)


class UserAgent(IAgentInterface):
    """
    Unified User Shopping & Stylist Agent.
    Binds all e-commerce tools (recommendations, cart management, negotiation, orders, auth)
    and operates directly on AgentState in a unified graph.
    """

    def __init__(self, llm, tools: Optional[List[Any]] = None):
        self.intent = "user_agent"

        # Resolve all available local tools if none explicitly provided
        if tools is not None:
            self.tools = list(tools)
        else:
            self.tools = []
            for module_name, getter_name in [
                ("Recommedation.tools", "get_recommendation_langchain_tools"),
                ("Cart.tools", "get_cart_langchain_tools"),
                ("Negotiation.tools", "get_negotiation_langchain_tools"),
                ("Order.tools", "get_order_langchain_tools"),
                ("Auth.tools", "get_auth_langchain_tools"),
            ]:
                try:
                    mod = __import__(module_name, fromlist=[getter_name])
                    getter = getattr(mod, getter_name)
                    self.tools.extend(getter())
                except Exception as e:
                    logger.warning("Could not load tools from %s: %s", module_name, e)

        # Deduplicate tools by name
        unique_tools = {}
        for t in self.tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
            if name:
                unique_tools[name] = t
        self.tools = list(unique_tools.values())

        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _detect_gender(self, messages: List[BaseMessage]) -> Optional[str]:
        """Detects if gender preference was explicitly mentioned in latest human messages."""
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

    def _build_prompt(self, state: AgentState) -> List[BaseMessage]:
        messages = state.get("messages", [])
        conversation_summary = state.get("conversation_summary")
        important_facts = state.get("important_facts")
        user_id = state.get("user_id")
        gender = state.get("gender")
        current_discount = state.get("current_discount_percent", 0.0) or 0.0
        customer_profile = state.get("customer_profile")
        is_authenticated = state.get("is_authenticated")

        # Dynamic customer session prompt enriched with authentication, profile state, and per-product discounts
        system_text = get_user_agent_prompt(
            user_id=user_id,
            gender=gender,
            current_discount=current_discount,
            customer_profile=customer_profile,
            is_authenticated=is_authenticated,
            negotiated_products=state.get("negotiated_products"),
            cart_global_discount=state.get("cart_global_discount_percent", 0.0) or 0.0,
        )

        return build_prompt_with_summary(
            system_text,
            messages,
            self.intent,
            conversation_summary=conversation_summary,
            important_facts=important_facts,
            last_recent_count=6,
            last_intent_count=6,
        )

    def run(self, state: AgentState) -> dict:
        messages = state.get("messages", [])
        prompt = self._build_prompt(state)
        response = self.llm.invoke(prompt)

        if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
            response.additional_kwargs = {}

        response.additional_kwargs["intent"] = self.intent

        updates = {
            "messages": [response],
            "intent": self.intent,
        }

        # Auto-detect gender if not yet set in state
        if not state.get("gender"):
            detected_gender = self._detect_gender(messages)
            if detected_gender:
                updates["gender"] = detected_gender

        return updates

    async def arun(self, state: AgentState) -> dict:
        messages = state.get("messages", [])
        prompt = self._build_prompt(state)
        if hasattr(self.llm, "ainvoke"):
            response = await self.llm.ainvoke(prompt)
        else:
            response = await asyncio.to_thread(self.llm.invoke, prompt)

        if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
            response.additional_kwargs = {}

        response.additional_kwargs["intent"] = self.intent

        updates = {
            "messages": [response],
            "intent": self.intent,
        }

        # Auto-detect gender if not yet set in state
        if not state.get("gender"):
            detected_gender = self._detect_gender(messages)
            if detected_gender:
                updates["gender"] = detected_gender

        return updates
