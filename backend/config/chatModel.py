import os
from dotenv import load_dotenv
from utils.chat_llm_model.factory import ChatModelFactory

load_dotenv()


class ChatModel:
    def __init__(self):
        load_dotenv()
        self._cached_large_chat_model = None
        self._cached_medium_chat_model = None
        self._cached_small_chat_model = None
        self.api_key = os.getenv("OPEN_ROUTER_KEYS") or os.getenv("OPEN_ROUTER_KEY")

    ## for getting the large chat model
    def get_large_chat_model(self):
        if self._cached_large_chat_model is None:
            self.api_key = self.api_key or os.getenv("OPEN_ROUTER_KEYS") or os.getenv("OPEN_ROUTER_KEY")
            self._cached_large_chat_model = ChatModelFactory.get_method(
                "openrouter",
                access_key=self.api_key,
                uri=self.api_key,
                model_name="dots-studio/dots-3-note-preview:free",
            )
        return self._cached_large_chat_model

    def _large_chat_model(self):
        return self.get_large_chat_model()

    ## for getting the medium chat model
    def get_medium_chat_model(self):
        if self._cached_medium_chat_model is None:
            self.api_key = self.api_key or os.getenv("OPEN_ROUTER_KEYS") or os.getenv("OPEN_ROUTER_KEY")
            self._cached_medium_chat_model = ChatModelFactory.get_method(
                "openrouter",
                access_key=self.api_key,
                uri=self.api_key,
                model_name="dots-studio/dots-3-note-preview:free",
            )
        return self._cached_medium_chat_model

    def _medium_chat_model(self):
        return self.get_medium_chat_model()

    ## for getting the small chat model
    def get_small_chat_model(self):
        if self._cached_small_chat_model is None:
            self.api_key = self.api_key or os.getenv("OPEN_ROUTER_KEYS") or os.getenv("OPEN_ROUTER_KEY")
            self._cached_small_chat_model = ChatModelFactory.get_method(
                "openrouter",
                access_key=self.api_key,
                uri=self.api_key, 
                model_name="cohere/north-mini-code:free"
            )
        return self._cached_small_chat_model

    def _small_chat_model(self):
        return self.get_small_chat_model()


chatModel = ChatModel()
