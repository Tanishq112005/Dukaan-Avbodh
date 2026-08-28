import os
from utils.chat_llm_model.factory import ChatModelFactory

class ChatModel: 
    def __init__(self):
        self._chat_model = None 
     
    def get_chat_model(self):
     
        if self._chat_model is None:
         
            api_key = os.getenv("GROQ_API_KEY") 
            
            self._chat_model = ChatModelFactory.get_method("groq", {
               "access_key": api_key
            })
            
        return self._chat_model
    
    
chatModel = ChatModel()     