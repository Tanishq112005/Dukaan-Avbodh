from agents.agentState import AgentState 
from config.chatModel import chatModel 


def general_node(state: AgentState):
    llm = chatModel.get_chat_model() 
    response = llm.invoke(state["messages"]).content
    return {"final_response": response}
