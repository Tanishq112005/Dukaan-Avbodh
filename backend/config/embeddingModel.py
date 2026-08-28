import os
from utils.embedding_model.factory import EmbeddingModelFactory

class EmbeddingModel: 
    def __init__(self):
        self._model = None
    
    def getModel(self):
        if self._model is None:
            api_key = os.getenv("HUGGINGFACE_API_KEY") 
            
            self._model = EmbeddingModelFactory.get_method("hugging_face", {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "api_key": api_key
            })
            
        return self._model
    
    
embeddingModel = EmbeddingModel()   