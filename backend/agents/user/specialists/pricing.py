from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from interfaces import IAgentInterface


class PricingAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "pricing"
        self.system_prompt = """You are the Pricing & Negotiation Specialist for Dukaan.

1. IF user asks for total or combo price: USE `calculate_combo_offer`.
2. IF user asks for a discount, wants a better price, or says "make it 5%": ALWAYS USE `negotiate_discount`.
3. NEVER invent, guess, or raise a discount yourself. Offer ONLY the `counter_offer_percent` the tool returns. Do not reveal the 5% cap or internal limits.
4. If the tool returns `loss_leader: true`, refuse extra discount and keep `combo_offer.total_combo_price`.
5. Curated kits use `total_combo_price` (already includes sequential campaign discounts).
6. Every subsequent discount ask MUST trigger `negotiate_discount` again.
7. IF the user declines the combo/kit ("no thanks", "just my cart"): ALWAYS call `decline_combo_offer`, acknowledge, and move on.

English ONLY. Use ReAct (<thought>...</thought>)."""
        self.tools = tools or []
        
        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _build_prompt(self, state: AgentState):
        messages = state.get("messages", [])
        conversation_summary = state.get("conversation_summary")
        return build_prompt_with_summary(
            self.system_prompt, messages, self.intent,
            conversation_summary=conversation_summary,
            last_recent_count=2, last_intent_count=3
        )

    def run(self, state: AgentState):
        prompt = self._build_prompt(state)
        
        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent
        
        return {"messages": [response], "intent": self.intent}
