## model factory , defing the models used 
from langchain_groq import ChatGroq
from .groq import Groq
from .openrouter import OpenRouter
from .google import Google
from .nvidia import Nvidia


class ChatModelFactory:
    
    @staticmethod
    def get_method(model_type: str, access_key: str):
        

        if model_type == "groq":
            model = Groq()
            model.setModel(
                uri=access_key , 
                
               )
            
            return model.getModel()
        
        elif model_type == "openrouter": 
           
            model =  OpenRouter() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        elif model_type == "google": 
           
            model =  Google() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        elif model_type == "nvidia":
            model =  Nvidia() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
             
            
        
        