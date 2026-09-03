## model factory , defing the models used 


class ChatModelFactory:
    
    @staticmethod
    def get_method(model_type: str, access_key: str):
        # Imports are deferred to each branch so that an unused provider's SDK
        # (e.g. langchain_google_genai) being missing from requirements.txt
        # can't crash startup for everyone — only that provider breaks, and only
        # if someone actually asks for it.

        if model_type == "groq":
            from .groq import Groq
            model = Groq()
            model.setModel(
                uri=access_key , 
                
               )
            
            return model.getModel()
        
        elif model_type == "openrouter": 
           
            from .openrouter import OpenRouter
            model =  OpenRouter() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        elif model_type == "google": 
           
            from .google import Google
            model =  Google() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
        
        elif model_type == "nvidia":
            from .nvidia import Nvidia
            model =  Nvidia() 
            model.setModel(uri=access_key)
            
            return model.getModel() 
             
            
        
        