import os
from utils.chat_llm_model.factory import ChatModelFactory

class ChatModel: 
    def __init__(self):
        self._chat_model = None 
     
    def get_chat_model(self):
     
        if self._chat_model is None:
            api_key = os.getenv("GOPEN_ROUTER_KEY") 
            self._chat_model = ChatModelFactory.get_method("openrouter", api_key)
            
        return self._chat_model
    
    
chatModel = ChatModel()     