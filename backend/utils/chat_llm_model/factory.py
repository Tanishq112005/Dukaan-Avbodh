## model factory , defing the models used 
from .openrouter import OpenRouter
from .groq import Groq
from .google import Google
from .nvidia import Nvidia


class ChatModelFactory:
    
    @staticmethod
    def get_method(model_type: str, access_key: str  , model_name: str = None):
        # Imports are deferred to each branch so that an unused provider's SDK
        # (e.g. langchain_google_genai) being missing from requirements.txt
        # can't crash startup for everyone — only that provider breaks, and only
        # if someone actually asks for it.

        if model_type == "groq":
            
            model = Groq()
            model.setModel(uri=access_key)
            
            return model.getModel()
        
        elif model_type == "openrouter": 
           
            
            model =  OpenRouter() 
            model.setModel(uri=access_key , model_name=model_name)
            
            return model.getModel() 
        
        elif model_type == "google": 
           
            model =  Google() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        elif model_type == "nvidia":
            
            model =  Nvidia() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        
            
             
            
        
        