from pydantic import BaseModel
### Hugging face base model  ### 

class HuggingFaceChatModelConfig(BaseModel):
    repo_id: str
    task: str 
    max_length: int 
    temperature: float
    
 
class HuggingFaceEmbeddingModelConfig(BaseModel):
    model_name : str 
        
class OpenRouterEmbeddingModelCofig(BaseModel):
    api_key : str
    
class JinaEmbeddingModelConfig(BaseModel):
    api_key : str 
    model_name : str 
    
    
        
    