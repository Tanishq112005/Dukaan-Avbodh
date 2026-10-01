import os
from utils.chat_llm_model.factory import ChatModelFactory

class ChatModel: 
    def __init__(self):
        self._large_chat_model = None 
        self._medium_chat_model = None 
        self._small_chat_model = None
        self.api_key = os.getenv("OPEN_ROUTER_KEYS")
    
        
    def get_large_chat_model(self):
     
        if self._large_chat_model is None:
            self._large_chat_model = ChatModelFactory.get_method("openrouter", uri=self.api_key , model_name="thinkingmachines/inkling:free") 
            
        return self._large_chat_model
    
    
    def get_medium_chat_model(self): 
        if self._medium_chat_model is None:
            self._medium_chat_model = ChatModelFactory.get_method("openrouter", uri=self.api_key , model_name="dots-studio/dots-3-note-preview:free") 
            
        return self._medium_chat_model
        
        
        
    def get_small_chat_model(self):
       
        if self._small_chat_model is None:
            self._small_chat_model = ChatModelFactory.get_method("openrouter", uri=self.api_key, model_name="cohere/north-mini-code:free")
            
        return self._small_chat_model
    
    
    
chatModel = ChatModel()     