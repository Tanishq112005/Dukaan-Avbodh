import logging
from typing import List, Optional

from langchain_core.messages import BaseMessage
from agents.user.interfaces import IAgentInterface
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary

from Cart.prompt import CART_SYSTEM_PROMPT, get_cart_prompt

logger = logging.getLogger(__name__)


class CartAgent(IAgentInterface):
    """
    Shopping Cart Specialist Agent.
    Implements IAgentInterface and operates on AgentState.
    """

    def __init__(self, llm, tools: Optional[List] = None):
        self.intent = "cart"
        self.system_prompt = CART_SYSTEM_PROMPT

        if tools is not None:
            self.tools = tools
        else:
            try:
                from Cart.tools import get_cart_langchain_tools
                self.tools = get_cart_langchain_tools()
            except ImportError:
                self.tools = []

        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _build_prompt(self, state: AgentState) -> List[BaseMessage]:
        messages = state.get("messages", [])
        conversation_summary = state.get("conversation_summary")
        important_facts = state.get("important_facts")
        user_id = state.get("user_id")

        # Injects dynamic user context into system prompt
        system_text = get_cart_prompt(user_id=user_id)

        return build_prompt_with_summary(
            system_text,
            messages,
            self.intent,
            conversation_summary=conversation_summary,
            important_facts=important_facts,
            last_recent_count=2,
            last_intent_count=3,
        )

    def run(self, state: AgentState) -> dict:
        prompt = self._build_prompt(state)
        response = self.llm.invoke(prompt)

        if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
            response.additional_kwargs = {}

        response.additional_kwargs["intent"] = self.intent

        return {
            "messages": [response],
            "intent": self.intent,
        }
