from langchain_openrouter import ChatOpenRouter
from .interfaces import IEmbedder


class OpenRouter(IEmbedder):
    
    def set_model(self, api_key: str):
        self._model = ChatOpenRouter(
            model="inclusionai/ling-3.0-flash-fin:free",
            api_key=api_key
        )
        
    def get_model(self):
        return self._model
    