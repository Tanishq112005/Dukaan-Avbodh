from langchain_core.messages import SystemMessage
from agents.user.agentState import AgentState
from utils.prompt_utils import filter_history_by_intent

class CartAgent:
    def __init__(self, llm, tools=None):
        self.intent = "cart"
        self.system_prompt = """You are the Cart Management Specialist for Dukaan.

1. USE `get_cart`, `add_to_cart`, `remove_from_cart`, and `update_cart_item_quantity` based on user requests.
2. NEVER say "I added it" unless you actually executed the `add_to_cart` tool successfully.
3. Ask for missing info (like size) BEFORE adding to cart.

English ONLY. Use ReAct (<thought>...</thought>)."""
        self.tools = tools or []
        
        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _build_prompt(self, messages):
        filtered_messages = filter_history_by_intent(messages, self.intent, last_recent_count=2, last_intent_count=3)
        return [SystemMessage(content=self.system_prompt)] + filtered_messages

    def run(self, state: AgentState):
        messages = state.get("messages", [])
        prompt = self._build_prompt(messages)
        
        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent
        
        return {"messages": [response], "intent": self.intent}
