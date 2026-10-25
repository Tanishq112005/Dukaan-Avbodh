import logging
from typing import List, Optional

from langchain_core.messages import BaseMessage
from agents.user.interfaces import IAgentInterface
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from Recommedation.tools import get_recommendation_langchain_tools
from Recommedation.prompt import RECOMMENDATION_SYSTEM_PROMPT, get_recommendation_prompt

logger = logging.getLogger(__name__)


class RecommendationAgent(IAgentInterface):
    """
    Recommendation & Product Discovery Specialist Agent.
    Implements IAgentInterface and operates on AgentState.
    """

    def __init__(self, llm, tools: Optional[List] = None):
        self.intent = "recommendation"
        self.system_prompt = RECOMMENDATION_SYSTEM_PROMPT

        if tools is not None:
            self.tools = tools
        else:
            try:
                self.tools = get_recommendation_langchain_tools()
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
        gender = state.get("gender")

        # Injects dynamic user context into system prompt if available
        system_text = get_recommendation_prompt(user_id=user_id, gender=gender)

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

        updates = {
            "messages": [response],
            "intent": self.intent,
        }
        if state.get("suggested_products"):
            updates["suggested_products"] = state.get("suggested_products")

        return updates
