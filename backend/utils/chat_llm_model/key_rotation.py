import asyncio
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

    On failure (bad key, rate limit, or a transient "Provider returned
    error" from the upstream model) it retries on the NEXT key/client in
    the rotation instead of blowing up the whole chat turn -- up to one
    full pass over all available keys, with a short backoff between
    attempts. Only raises if every key in the rotation fails.
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
        last_err = None
        n = len(self._clients)
        for attempt in range(n):
            client = self._next_client()
            try:
                return await client.ainvoke(*args, **kwargs)
            except Exception as e:
                last_err = e
                print(f"[{self._label}] ainvoke attempt {attempt + 1}/{n} failed: {e}")
                if attempt < n - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise last_err

    def invoke(self, *args, **kwargs):
        last_err = None
        n = len(self._clients)
        for attempt in range(n):
            client = self._next_client()
            try:
                return client.invoke(*args, **kwargs)
            except Exception as e:
                last_err = e
                print(f"[{self._label}] invoke attempt {attempt + 1}/{n} failed: {e}")
        raise last_err

    async def astream(self, *args, **kwargs):
        last_err = None
        n = len(self._clients)
        for attempt in range(n):
            client = self._next_client()
            try:
                async for chunk in client.astream(*args, **kwargs):
                    yield chunk
                return
            except Exception as e:
                last_err = e
                print(f"[{self._label}] astream attempt {attempt + 1}/{n} failed: {e}")
                if attempt < n - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise last_err

    def stream(self, *args, **kwargs):
        last_err = None
        n = len(self._clients)
        for attempt in range(n):
            client = self._next_client()
            try:
                yield from client.stream(*args, **kwargs)
                return
            except Exception as e:
                last_err = e
                print(f"[{self._label}] stream attempt {attempt + 1}/{n} failed: {e}")
        raise last_err
