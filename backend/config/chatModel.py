import os
from utils.chat_llm_model.factory import ChatModelFactory

class ChatModel: 
    def __init__(self):
        self._chat_model = None 
        self._small_chat_model = None
     
    def get_chat_model(self):
     
        if self._chat_model is None:
            api_key = os.getenv("OPEN_ROUTER_KEYS")
            self._chat_model = ChatModelFactory.get_method("openrouter", api_key)
            
        return self._chat_model
        
    def get_small_chat_model(self):
        if self._small_chat_model is None:
            api_key = os.getenv("OPEN_ROUTER_KEYS")
            # Using a fast, small model for routing and general queries
            self._small_chat_model = ChatModelFactory.get_method("meta", api_key)
            
        return self._small_chat_model
    
    
chatModel = ChatModel()     