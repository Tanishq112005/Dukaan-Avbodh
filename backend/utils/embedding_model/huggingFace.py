from .interfaces import IEmbedder
from  langchain_huggingface import HuggingFaceEndpointEmbeddings


class HuggingFace(IEmbedder):
    
    def set_model(self, model_name: str, api_key: str):
        self.__model = HuggingFaceEndpointEmbeddings(
            model=model_name,
            huggingfacehub_api_token=api_key
        )
        
    
        

    
        