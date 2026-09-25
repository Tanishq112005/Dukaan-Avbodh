from .interfaces import IEmbedder
from langchain_community.embeddings import JinaEmbeddings
import os 
# Set your API key in the environment


class Jina(IEmbedder):
    
    def set_model(self, model_name: str, api_key: str):
        self._model = JinaEmbeddings(
            model=model_name,
            jina_api_key=api_key
        )
        
    def get_model(self):
        return self._model