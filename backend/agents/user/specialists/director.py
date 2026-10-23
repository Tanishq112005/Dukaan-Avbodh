from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import filter_history_by_intent
from .interfaces import IAgentInterface
from pydantic import BaseModel, Field
from typing import Literal

class Route(BaseModel):
    """Route the user's request to the appropriate specialist."""
    intent: Literal["product_search", "cart_editing", "pricing_negotiation", "payment", "register", "general_query"] = Field(
        description="The specialized agent to route to based on the user's request."
    )


class DirectorAgent(IAgentInterface):
    def __init__(self, llm):
        self.intent = "director"
        self.system_prompt = """You are the intelligent Router. Analyze the user's request and classify it into ONE intent:
                              - 'product_search': Finding products, asking about categories, or needing recommendations.
                              - 'cart_editing': Adding, removing, or updating items in the cart.
                              - 'pricing_negotiation': Asking for discounts, combo offers, or negotiating prices.
                              - 'payment': Creating an order or checking payment/checkout status.
                              - 'register': Registering a new account or updating user profile details.
                              - 'general_query': Greetings, casual chat, or general questions."""
        
                                   
        self.llm = llm.with_structured_output(Route)

    def _build_prompt(self, messages):
        filtered_messages = filter_history_by_intent(messages, self.intent, last_recent_count=4, last_intent_count=0)
        return [SystemMessage(content=self.system_prompt)] + filtered_messages

    def run(self, state: AgentState):
        messages = state.get("messages", [])
        prompt = self._build_prompt(messages)
        
        # The Director uses structured output, so response is a Route object, not an AIMessage.
        # We do NOT append this to the chat history, so it remains invisible to the user.
        route_obj = self.llm.invoke(prompt)
        
        return {"intent": route_obj.intent}
