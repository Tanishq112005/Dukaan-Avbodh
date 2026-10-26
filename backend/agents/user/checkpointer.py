import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv()

# --- Patch redisvl for Aiven / Redis 7.2+ missing index error format ---
try:
    import redisvl.exceptions
    if "not found in database" not in redisvl.exceptions._MISSING_INDEX_ERROR_FRAGMENTS:
        redisvl.exceptions._MISSING_INDEX_ERROR_FRAGMENTS = (
            *redisvl.exceptions._MISSING_INDEX_ERROR_FRAGMENTS,
            "not found in database",
            "not found",
        )
except Exception:
    pass

from pymongo import MongoClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

try:
    from langgraph.checkpoint.mongodb import MongoDBSaver

    async def _aget_tuple(self, config):
        return await asyncio.to_thread(self.get_tuple, config)

    async def _aput(self, config, checkpoint, metadata, new_versions):
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def _aput_writes(self, config, writes, task_id):
        return await asyncio.to_thread(self.put_writes, config, writes, task_id)

    MongoDBSaver.aget_tuple = _aget_tuple
    MongoDBSaver.aput = _aput
    MongoDBSaver.aput_writes = _aput_writes
except (ImportError, ModuleNotFoundError):
    MongoDBSaver = None

try:
    from langgraph.checkpoint.redis import RedisSaver

    async def _redis_aget_tuple(self, config):
        return await asyncio.to_thread(self.get_tuple, config)

    async def _redis_aput(self, config, checkpoint, metadata, new_versions):
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def _redis_aput_writes(self, config, writes, task_id):
        return await asyncio.to_thread(self.put_writes, config, writes, task_id)

    RedisSaver.aget_tuple = _redis_aget_tuple
    RedisSaver.aput = _redis_aput
    RedisSaver.aput_writes = _redis_aput_writes
except (ImportError, ModuleNotFoundError):
    RedisSaver = None

logger = logging.getLogger(__name__)

# --- Monkey-patch JsonPlusSerializer for serialization compatibility ---
if not hasattr(JsonPlusSerializer, "dumps"):
    JsonPlusSerializer.dumps = JsonPlusSerializer.dumps_typed
if not hasattr(JsonPlusSerializer, "loads"):
    JsonPlusSerializer.loads = JsonPlusSerializer.loads_typed


class AgentCheckPointer:
    """
    Manages LangGraph checkpointers for persisting conversation state.
    Provides fast MemorySaver for zero-latency in-memory state transitions during live execution,
    with RedisCheckPointer (RedisSaver) and MongoDBCheckPointer (MongoDBSaver) available for persistence.
    """

    def __init__(self):
        # In-memory checkpointer
        self._in_memory: Optional[MemorySaver] = None

        # MongoDB configurations
        self.mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_memory: Optional[Any] = None

        # Redis configurations
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_memory: Optional[Any] = None
        self.checkpoint_prefix = os.getenv("REDIS_CHECKPOINT_PREFIX", "checkpoint:user_agent")
        self.checkpoint_write_prefix = os.getenv(
            "REDIS_CHECKPOINT_WRITE_PREFIX", "checkpoint_write:user_agent"
        )
        ttl_seconds = int(os.getenv("REDIS_CHECKPOINT_TTL", "86400"))
        self.ttl = {"checkpoint": ttl_seconds, "checkpoint_write": ttl_seconds}

    def getMemorySaver(self) -> MemorySaver:
        """
        Initializes and returns a shared in-memory checkpointer.
        Eliminates network and serialization overhead during live graph execution.
        """
        if self._in_memory is None:
            self._in_memory = MemorySaver()
        return self._in_memory

    def getRedisCheckPointer(
        self,
        redis_url: Optional[str] = None,
        checkpoint_prefix: Optional[str] = None,
        checkpoint_write_prefix: Optional[str] = None,
        ttl: Optional[Dict[str, int]] = None,
    ) -> BaseCheckpointSaver:
        """
        Initializes and returns the RedisSaver checkpointer configured with
        connection URL, keyspace prefixes, and TTL values.
        """
        if self.redis_memory is not None:
            return self.redis_memory

        if RedisSaver is None:
            raise ImportError("langgraph.checkpoint.redis is not installed")

        url = redis_url or self.redis_url
        prefix = checkpoint_prefix or self.checkpoint_prefix
        write_prefix = checkpoint_write_prefix or self.checkpoint_write_prefix
        ttl_dict = ttl or self.ttl

        self.redis_memory = RedisSaver(
            redis_url=url,
            checkpoint_prefix=prefix,
            checkpoint_write_prefix=write_prefix,
            ttl=ttl_dict,
        )
        try:
            self.redis_memory.setup()
            logger.info("RedisSaver RediSearch indexes verified/created successfully.")
        except Exception as e:
            logger.warning("RedisSaver.setup() encountered warning: %s", e)

        return self.redis_memory

    def getMongoDBCheckPointer(self) -> BaseCheckpointSaver:
        """
        Initializes and returns the MongoDB checkpointer.
        """
        if self.mongodb_memory is not None:
            return self.mongodb_memory

        if MongoDBSaver is None:
            raise ImportError("langgraph.checkpoint.mongodb is not installed")

        sync_client = MongoClient(self.mongo_uri)
        self.mongodb_memory = MongoDBSaver(sync_client)
        return self.mongodb_memory

    def getCheckPointer(self, prefer: str = "memory") -> BaseCheckpointSaver:
        """
        Returns the active checkpointer passed to workflow.compile(checkpointer=...).
        Defaults to in-memory checkpointer for ultra-fast, zero-I/O execution.
        Persistence is handled asynchronously at the end of the turn.
        """
        prefer_type = os.getenv("CHECKPOINTER_TYPE", prefer).lower()

        if prefer_type == "memory":
            return self.getMemorySaver()

        if prefer_type == "redis":
            try:
                return self.getRedisCheckPointer()
            except Exception as e:
                logger.warning(
                    "Redis checkpointer initialization failed (%s); falling back to MemorySaver.",
                    e,
                )
                return self.getMemorySaver()

        if prefer_type == "mongodb":
            try:
                return self.getMongoDBCheckPointer()
            except Exception as e:
                logger.warning(
                    "MongoDB checkpointer initialization failed (%s); falling back to MemorySaver.",
                    e,
                )
                return self.getMemorySaver()

        return self.getMemorySaver()


checkPointer = AgentCheckPointer()
