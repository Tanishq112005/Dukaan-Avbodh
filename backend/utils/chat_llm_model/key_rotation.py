import itertools
from threading import Lock


class KeyRotator:
    """Thread-safe circular index generator: 0, 1, 2, ..., n-1, 0, 1, 2, ..."""
    def __init__(self, n: int):
        if n < 1:
            raise ValueError("KeyRotator needs at least 1 key")
        self._n = n
        self._counter = itertools.count()
        self._lock = Lock()

    def next_index(self) -> int:
        with self._lock:
            return next(self._counter) % self._n


class RotatingChatModel:
    """
    Generic key-rotation wrapper for ANY LangChain chat model.

    Give it a list of API keys and a `client_builder(key) -> chat_model`
    function; it builds one client per key up front and round-robins
    between them on every invoke/ainvoke/stream call. The provider-
    specific construction logic lives in client_builder, so this class
    doesn't need to know anything about OpenRouter vs Nvidia vs Groq.
    """

    def __init__(self, api_keys, client_builder, _bound_tools=None, _label="model"):
        if not api_keys:
            raise ValueError("RotatingChatModel needs at least one API key")
        self._api_keys = api_keys
        self._client_builder = client_builder
        self._bound_tools = _bound_tools
        self._label = _label

        self._clients = [self._build_client(k) for k in api_keys]
        self._rotator = KeyRotator(len(self._clients))

    def _build_client(self, key):
        client = self._client_builder(key)
        if self._bound_tools:
            client = client.bind_tools(self._bound_tools)
        return client

    def _next_client(self):
        idx = self._rotator.next_index()
        print(f"[{self._label}] Routing request to key #{idx + 1}/{len(self._clients)}")
        return self._clients[idx]

    def bind_tools(self, tools, **kwargs):
        # Rebuild all N clients with tools bound, so every key in the
        # rotation stays tool-call-capable.
        return RotatingChatModel(
            api_keys=self._api_keys,
            client_builder=self._client_builder,
            _bound_tools=tools,
            _label=self._label,
        )

    async def ainvoke(self, *args, **kwargs):
        return await self._next_client().ainvoke(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self._next_client().invoke(*args, **kwargs)

    async def astream(self, *args, **kwargs):
        async for chunk in self._next_client().astream(*args, **kwargs):
            yield chunk

    def stream(self, *args, **kwargs):
        yield from self._next_client().stream(*args, **kwargs)