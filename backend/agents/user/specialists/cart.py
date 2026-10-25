from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from ..interfaces import IAgentInterface
from Cart.prompt import CART_SYSTEM_PROMPT


class CartAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "cart"
        self.system_prompt = CART_SYSTEM_PROMPT
        self.tools = tools or []
        
        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _build_prompt(self, state: AgentState):
        messages = state.get("messages", [])
        conversation_summary = state.get("conversation_summary")
        important_facts = state.get("important_facts")
        return build_prompt_with_summary(
            self.system_prompt, messages, self.intent,
            conversation_summary=conversation_summary,
            important_facts=important_facts,
            last_recent_count=2, last_intent_count=3
        )

    def run(self, state: AgentState):
        prompt = self._build_prompt(state)
        
        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent
        
        return {"messages": [response], "intent": self.intent}
