from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from .interfaces import IAgentInterface


class PaymentAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "payment"
        self.system_prompt = """You are the Checkout & Payment Specialist for Dukaan.

1. You handle `create_order` and `check_payment_status`.
2. NEVER call `create_order` unless you are absolutely sure the user's profile/address is complete.
3. After `create_order`, share the `payment_link` as a markdown link: [Pay now](THE_URL) and print the URL on its own line. Tell them to tap it, pay, and return.
4. If the user says they paid, or you receive [SYSTEM EVENT: payment], immediately call `check_payment_status`.
5. If paid=true: congratulate them. If paid=false: politely tell them payment is not confirmed yet and reshare the link.

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
            self.system_prompt,
            messages,
            self.intent,
            conversation_summary=conversation_summary,
            last_recent_count=2,
            last_intent_count=3,
        )

    def run(self, state: AgentState):
        prompt = self._build_prompt(state)

        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent

        return {"messages": [response], "intent": self.intent}
