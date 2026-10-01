from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from interfaces import IAgentInterface

class RegisterAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "register"
        self.system_prompt = """You are the Registration & Profile Specialist for Dukaan.

1. When the user wants to buy / checkout, you MUST ensure their details are complete by calling `get_user_details`.
2. IF `is_complete` is true: show their name, email, and address, then ask ONLY for confirmation: "Shall I place the order to this address, or do you want to change it?"
3. IF they want to change OR if information is missing (`missing_fields`): ask ONLY for the missing/changed fields. Do not re-ask for details you already have.
4. After they provide fields, call `update_user_details`.
5. Once details are fully confirmed and complete, tell the user you are ready and they will be routed to Payment.

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
