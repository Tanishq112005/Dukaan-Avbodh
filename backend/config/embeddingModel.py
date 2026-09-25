import os
from utils.embedding_model.factory import EmbeddingModelFactory
from sentence_transformers import SentenceTransformer
class EmbeddingModel: 
    def __init__(self):
        self._model = None
    
    def getModel(self):
        if self._model is None:
            self._model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
        return self._model
    
    
embeddingModel = EmbeddingModel()   