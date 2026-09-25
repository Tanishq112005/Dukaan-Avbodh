from langchain_core.messages import SystemMessage
from agents.user.agentState import AgentState

class DirectorPromptHandler:
    def __init__(self):
        self.intent = "director"
        self.system_prompt = """You are the Director. Analyze the user's request and route them to the correct specialist."""

    def build_prompt(self, messages):
        # Director only needs the most recent context to route efficiently
        recent_messages = messages[-2:] if len(messages) >= 2 else messages
        return [SystemMessage(content=self.system_prompt)] + recent_messages


class DirectorAgent:
    def __init__(self, llm):
        self.intent = "director"
        self.prompt_handler = DirectorPromptHandler()
        self.llm = llm 

    def run(self, state: AgentState):
        messages = state.get("messages", [])
        prompt = self.prompt_handler.build_prompt(messages)
        
        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent
        
        return {"messages": [response], "intent": self.intent}
