from agents.agentState import AgentState 
from config.chatModel import chatModel 
from langchain_core.messages import SystemMessage


def general_node(state: AgentState):
    llm = chatModel.get_chat_model() 
    
    # Prepend a system instruction to force English
    system_msg = SystemMessage(content="You are a helpful AI fashion assistant on an e-commerce clothing store called Dukaan. Respond ONLY in English. Keep responses short and friendly.")
    messages = [system_msg] + state["messages"]
    
    response = llm.invoke(messages).content
    return {"final_response": response}
