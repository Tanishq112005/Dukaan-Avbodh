from langchain_google_genai import ChatGoogleGenerativeAI
from .interfaces import IChatModels

class Google(IChatModels):
    
    api_key : str 
    model : ChatGoogleGenerativeAI
    
    def setModel(self , uri: str):
        try:
            self.api_key = uri
            print("Initalizing the model")
            self.model = ChatGoogleGenerativeAI(
                api_key=self.api_key, 
                model="gemini-3.8-flash", 
                thinking_level='medium'      
            )
            
            print("Initilization is completed") 
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq client: {e}")
        
    def getModel(self): 
        return self.model 
    
 
    
    
    
                         

            
        