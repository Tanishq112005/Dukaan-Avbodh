from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary

class CartAgent:
    def __init__(self, llm, tools=None):
        self.intent = "cart"
        self.system_prompt = """You are the Cart Management Specialist for Dukaan.
1. USE `get_cart`, `add_to_cart`, `remove_from_cart`, and `update_cart_item_quantity` based on user requests.
2. NEVER say "I added it" unless you actually executed the `add_to_cart` tool successfully.
3. Ask for missing info (like size) BEFORE adding to cart.
"""
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
