from langchain_openrouter import ChatOpenRouter
from .interfaces import IChatModels



class OpenRouter(IChatModels):
    
    model : ChatOpenRouter 
    apiKey : str 
    
    def setModel(self , uri : str ):
        self.apiKey = uri  
        try:
            print("Initalizing the model")
            
            self.model = ChatOpenRouter(
                 model="dots-studio/dots-3-note-preview:free", 
                 api_key=self.apiKey,
                 temperature=0,
                 max_tokens=2048,
            )
            
            print("Initilization is completed") 
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenRouter client: {e}")
        
    def getModel(self): 
        return self.model