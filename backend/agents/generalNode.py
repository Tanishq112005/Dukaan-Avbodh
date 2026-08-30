from agents.agentState import AgentState 
from config.chatModel import chatModel 
from langchain_core.messages import SystemMessage


def general_node(state: AgentState):
    llm = chatModel.get_chat_model() 
    
    # Prepend a system instruction to force English
    system_msg = SystemMessage(content="You are a helpful AI fashion assistant on an e-commerce clothing store called Dukaan. Respond ONLY in English. Keep responses short and friendly And if the user is ask for the something the E-commerce platform of the clothes do not do , please do not answer , even the questions like who is the prime minister of the india and all .")
    messages = [system_msg] + state["messages"]
    
    response = llm.invoke(messages).content
    return {"final_response": response}
