from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from interfaces import IAgentInterface

class ProductAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "product"
        self.system_prompt = """You are the Product Discovery Specialist for Dukaan.
    
1. IF user explicitly asks for a specific item (e.g., "show me blue jeans"): USE `get_products_by_type` or `search_products`. 
   DO NOT hallucinate products or brands. YOU MUST CALL A TOOL to see what's in stock before answering.
2. IF frontend triggers [SYSTEM EVENT] OR user asks for general suggestions: USE `recommend_products`.
3. NEVER list product details manually in text; the UI handles it.

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
