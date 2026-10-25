import os
import asyncio
import logging
from typing import Optional, Dict
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
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

logger = logging.getLogger(__name__)

# --- Monkey-patch MongoDBSaver for async support ---
async def _aget_tuple(self, config):
    return await asyncio.to_thread(self.get_tuple, config)

async def _aput(self, config, checkpoint, metadata, new_versions):
    return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

async def _aput_writes(self, config, writes, task_id):
    return await asyncio.to_thread(self.put_writes, config, writes, task_id)

MongoDBSaver.aget_tuple = _aget_tuple
MongoDBSaver.aput = _aput
MongoDBSaver.aput_writes = _aput_writes

# --- Monkey-patch RedisSaver for async support ---
async def _redis_aget_tuple(self, config):
    return await asyncio.to_thread(self.get_tuple, config)

async def _redis_aput(self, config, checkpoint, metadata, new_versions):
    return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

async def _redis_aput_writes(self, config, writes, task_id):
    return await asyncio.to_thread(self.put_writes, config, writes, task_id)

RedisSaver.aget_tuple = _redis_aget_tuple
RedisSaver.aput = _redis_aput
RedisSaver.aput_writes = _redis_aput_writes

# --- Monkey-patch JsonPlusSerializer for serialization compatibility ---
if not hasattr(JsonPlusSerializer, "dumps"):
    JsonPlusSerializer.dumps = JsonPlusSerializer.dumps_typed
if not hasattr(JsonPlusSerializer, "loads"):
    JsonPlusSerializer.loads = JsonPlusSerializer.loads_typed


class AgentCheckPointer:
    """
    Manages LangGraph checkpointers for persisting conversation state.
    Supports RedisCheckPointer (RedisSaver) with configurable connection parameters,
    MongoDBCheckPointer (MongoDBSaver), and in-memory fallback.
    """

    def __init__(self):
        # MongoDB configurations
        self.mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_memory: Optional[MongoDBSaver] = None

        # Redis configurations
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_memory: Optional[RedisSaver] = None
        self.checkpoint_prefix = os.getenv("REDIS_CHECKPOINT_PREFIX", "checkpoint:user_agent")
        self.checkpoint_write_prefix = os.getenv(
            "REDIS_CHECKPOINT_WRITE_PREFIX", "checkpoint_write:user_agent"
        )
        ttl_seconds = int(os.getenv("REDIS_CHECKPOINT_TTL", "86400"))
        self.ttl = {"checkpoint": ttl_seconds, "checkpoint_write": ttl_seconds}

    def getRedisCheckPointer(
        self,
        redis_url: Optional[str] = None,
        checkpoint_prefix: Optional[str] = None,
        checkpoint_write_prefix: Optional[str] = None,
        ttl: Optional[Dict[str, int]] = None,
    ) -> RedisSaver:
        """
        Initializes and returns the RedisSaver checkpointer configured with
        connection URL, keyspace prefixes, and TTL values.
        """
        if self.redis_memory is not None:
            return self.redis_memory

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

    def getMongoDBCheckPointer(self) -> MongoDBSaver:
        """
        Initializes and returns the MongoDB checkpointer.
        """
        if self.mongodb_memory is not None:
            return self.mongodb_memory

        sync_client = MongoClient(self.mongo_uri)
        self.mongodb_memory = MongoDBSaver(sync_client)
        return self.mongodb_memory

    def getCheckPointer(self, prefer: str = "redis") -> BaseCheckpointSaver:
        """
        Returns the active checkpointer passed to workflow.compile(checkpointer=...).
        Prefers Redis by default, with graceful fallback to MongoDB or MemorySaver.
        """
        prefer_type = os.getenv("CHECKPOINTER_TYPE", prefer).lower()

        if prefer_type == "redis":
            try:
                return self.getRedisCheckPointer()
            except Exception as e:
                logger.warning(
                    "Redis checkpointer initialization failed (%s); falling back to MongoDB/MemorySaver.",
                    e,
                )

        try:
            return self.getMongoDBCheckPointer()
        except Exception as e:
            logger.warning(
                "MongoDB checkpointer initialization failed (%s); falling back to MemorySaver.",
                e,
            )
            return MemorySaver()


checkPointer = AgentCheckPointer()
