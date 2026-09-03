from langchain_openai import ChatOpenAI
from utils.chat_llm_model.interfaces import IChatModels




class Nvidia(IChatModels):
    
    api_key : str 
    model : ChatOpenAI
    
    def setModel(self , uri: str):
        try:
            self.api_key = uri
            print("Initalizing the model")
            self.model = ChatOpenAI(
              openai_api_base="https://api.anyapi.ai/v1",
              model="google/gemma-4-26b-a4b-it:free",
              openai_api_key=self.api_key,
               temperature=0,
                timeout=None)
            
            print("Initilization is completed") 
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Nvidia client: {e}")
        
    def getModel(self): 
        return self.model 
    
 
    
    
    
                         

            
        