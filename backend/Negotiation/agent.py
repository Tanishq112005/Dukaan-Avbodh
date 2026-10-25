import logging
from typing import List, Optional

from langchain_core.messages import BaseMessage
from agents.user.interfaces import IAgentInterface
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary

from Negotiation.prompt import NEGOTIATION_SYSTEM_PROMPT, get_negotiation_prompt

logger = logging.getLogger(__name__)


class NegotiationAgent(IAgentInterface):
    """
    Pricing & Negotiation Specialist Agent.
    Implements IAgentInterface and operates on AgentState.
    """

    def __init__(self, llm, tools: Optional[List] = None):
        self.intent = "pricing"
        self.system_prompt = NEGOTIATION_SYSTEM_PROMPT

        if tools is not None:
            self.tools = tools
        else:
            try:
                from Negotiation.tools import get_negotiation_langchain_tools
                self.tools = get_negotiation_langchain_tools()
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
        current_discount = state.get("current_discount_percent", 0.0) or 0.0

        # Injects dynamic user negotiation context
        system_text = get_negotiation_prompt(user_id=user_id, current_discount=current_discount)

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
