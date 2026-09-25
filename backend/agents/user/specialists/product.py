from langchain_core.messages import SystemMessage
from agents.user.agentState import AgentState

class ProductPromptHandler:
    def __init__(self):
        self.intent = "product"
        self.system_prompt = "You are the Product Specialist. Help the user find and discover products."

    def build_prompt(self, messages):
        """Filters history for product-intent messages + the latest 2 messages."""
        filtered = []
        total_msgs = len(messages)
        for i, msg in enumerate(messages):
            is_recent = (i >= total_msgs - 2)
            msg_intent = msg.additional_kwargs.get("intent")
            if is_recent or msg_intent == self.intent:
                filtered.append(msg)
                
        return [SystemMessage(content=self.system_prompt)] + filtered


class ProductAgent:
    def __init__(self, llm, tools=None):
        self.intent = "product"
        self.prompt_handler = ProductPromptHandler()
        self.tools = tools or []
        
        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def run(self, state: AgentState):
        messages = state.get("messages", [])
        prompt = self.prompt_handler.build_prompt(messages)
        
        response = self.llm.invoke(prompt)
        response.additional_kwargs["intent"] = self.intent
        
        return {"messages": [response]}
