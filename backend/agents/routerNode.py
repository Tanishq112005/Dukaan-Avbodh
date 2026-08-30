from agents.agentState import AgentState
from typing import Literal
from pydantic import BaseModel
from config.chatModel import chatModel 


class RouterOutput(BaseModel):
    intent: Literal["SEARCH", "RECOMMEND", "NEGOTIATE", "GENERAL"]



def router_node(state: AgentState):
    
    llm = chatModel.get_chat_model() 
    """Analyzes the latest user message and decides the route."""
    
    if not state.get("messages") or not state["messages"][-1].content:
        return {"intent": "RECOMMEND"}

    last_message = state["messages"][-1].content
    
    if last_message == "PROACTIVE_SUGGESTION_TRIGGER":
        return {"intent": "RECOMMEND"}
    
    prompt = f"""You are an intent router for a clothing store.
    Categorize the following user message into ONE of these intents:
    - SEARCH: User is looking for a specific item (e.g., 'black tie', 'show me jeans').
    - NEGOTIATE: User is asking for discounts, OR the user is accepting/agreeing to a recommendation (e.g., 'Yes I like it', 'Ok add it', 'Sure').
    - RECOMMEND: User asks for suggestions or what matches their current cart , and if the user ask for the giving the total combo offer price .
    - GENERAL: General chat, greetings, unclear intent, or rejecting a product/offer (e.g., "I don't like this", "no thanks") .
    
    User Message: {last_message}
    """
    structured_llm = llm.with_structured_output(RouterOutput)
    result = structured_llm.invoke(prompt)
    
    return {"intent": result.intent}

def route_decision(state: AgentState) -> str:
    return state["intent"]
