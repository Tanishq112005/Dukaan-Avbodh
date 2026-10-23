from langchain_core.messages import SystemMessage
from agents.user.state import AgentState
from utils.prompt_utils import build_prompt_with_summary
from .interfaces import IAgentInterface


class GeneralAgent(IAgentInterface):
    def __init__(self, llm, tools=None):
        self.intent = "general"
        self.system_prompt = """You are the friendly, proactive, and witty sales stylist for Dukaan, a premium clothing and fashion store.

You handle casual chat, greetings, and general questions.
- You CANNOT browse the web or look up external links.
- You have NO tools. If the user wants to search products, check cart, negotiate, or pay, you must politely inform them that you are ready to help with that, and the system will route them automatically on the next turn.

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
            last_recent_count=6,
            last_intent_count=0,
        )

    def run(self, state: AgentState):
        prompt = self._build_prompt(state)

        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent

        return {"messages": [response], "intent": self.intent}
