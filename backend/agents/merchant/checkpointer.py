import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv()

from pymongo import MongoClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# --- Patch JsonPlusSerializer for serialization compatibility ---
if not hasattr(JsonPlusSerializer, "dumps"):
    JsonPlusSerializer.dumps = JsonPlusSerializer.dumps_typed
if not hasattr(JsonPlusSerializer, "loads"):
    JsonPlusSerializer.loads = JsonPlusSerializer.loads_typed

# --- Patch MongoDBSaver for async execution ---
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

# --- Patch RedisSaver for async execution ---
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


class MerchantCheckPointer:
    """
    Manages LangGraph checkpointers for persisting Merchant Agent conversation state.
    Provides fast in-memory checkpointer for zero-latency execution transitions,
    with MongoDB and Redis options for persistent multi-turn storage.
    """

    def __init__(self):
        self._in_memory: Optional[MemorySaver] = None
        self.mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_memory: Optional[Any] = None
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_memory: Optional[Any] = None
        self.checkpoint_prefix = os.getenv("REDIS_MERCHANT_CHECKPOINT_PREFIX", "checkpoint:merchant_agent")
        self.checkpoint_write_prefix = os.getenv(
            "REDIS_MERCHANT_CHECKPOINT_WRITE_PREFIX", "checkpoint_write:merchant_agent"
        )
        ttl_seconds = int(os.getenv("REDIS_CHECKPOINT_TTL", "86400"))
        self.ttl = {"checkpoint": ttl_seconds, "checkpoint_write": ttl_seconds}

    def getMemorySaver(self) -> MemorySaver:
        """Initializes and returns a shared in-memory checkpointer."""
        if self._in_memory is None:
            self._in_memory = MemorySaver()
        return self._in_memory

    def getMongoDBCheckPointer(self) -> BaseCheckpointSaver:
        """Initializes and returns the MongoDB checkpointer for merchant session memory."""
        if self.mongodb_memory is not None:
            return self.mongodb_memory

        if MongoDBSaver is None:
            raise ImportError("langgraph.checkpoint.mongodb is not installed")

        sync_client = MongoClient(self.mongo_uri)
        self.mongodb_memory = MongoDBSaver(sync_client)
        return self.mongodb_memory

    def getRedisCheckPointer(self) -> BaseCheckpointSaver:
        """Initializes and returns RedisSaver checkpointer."""
        if self.redis_memory is not None:
            return self.redis_memory

        if RedisSaver is None:
            raise ImportError("langgraph.checkpoint.redis is not installed")

        self.redis_memory = RedisSaver(
            redis_url=self.redis_url,
            checkpoint_prefix=self.checkpoint_prefix,
            checkpoint_write_prefix=self.checkpoint_write_prefix,
            ttl=self.ttl,
        )
        try:
            self.redis_memory.setup()
        except Exception as e:
            logger.warning("Merchant RedisSaver setup warning: %s", e)

        return self.redis_memory

    def getCheckPointer(self, prefer: str = "memory") -> BaseCheckpointSaver:
        """
        Returns checkpointer instance for workflow compilation.
        Defaults to 'memory' for ultra-fast, zero-overhead execution.
        """
        prefer_type = os.getenv("CHECKPOINTER_TYPE", prefer).lower()

        if prefer_type == "mongodb":
            try:
                return self.getMongoDBCheckPointer()
            except Exception as e:
                logger.warning("MongoDB checkpointer failed (%s); falling back to MemorySaver.", e)
                return self.getMemorySaver()

        if prefer_type == "redis":
            try:
                return self.getRedisCheckPointer()
            except Exception as e:
                logger.warning("Redis checkpointer failed (%s); falling back to MemorySaver.", e)
                return self.getMemorySaver()

        return self.getMemorySaver()


checkPointer = MerchantCheckPointer()
