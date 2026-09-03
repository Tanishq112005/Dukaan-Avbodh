from langchain_openrouter import ChatOpenRouter
from .interfaces import IChatModels
from .key_rotation import RotatingChatModel

DEFAULT_MODEL = "dots-studio/dots-3-note-preview:free"


class OpenRouter(IChatModels):

    model: RotatingChatModel
    apiKeys: list

    def setModel(self, uri=None, model=DEFAULT_MODEL, temperature=0, max_tokens=2048):
        """
        uri: comma-separated string of OpenRouter API keys, e.g.
             "sk-or-key1,sk-or-key2,sk-or-key3,sk-or-key4,sk-or-key5,sk-or-key6"
        """
        try:
            print("Initalizing the model")
            keys = [k.strip() for k in (uri or "").split(",") if k.strip()]
            if not keys:
                raise ValueError("No OpenRouter API key(s) provided")

            self.apiKeys = keys

            def build_client(key):
                return ChatOpenRouter(
                    api_key=key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            self.model = RotatingChatModel(
                api_keys=keys,
                client_builder=build_client,
                _label="OpenRouter",
            )

            print(f"Initilization is completed with {len(keys)} rotating key(s)")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenRouter client: {e}")

    def getModel(self):
        return self.model