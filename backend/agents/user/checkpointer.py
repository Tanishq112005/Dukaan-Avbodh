import os
import asyncio
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

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

# --- Monkey-patch JsonPlusSerializer for serialization compatibility ---
if not hasattr(JsonPlusSerializer, "dumps"):
    JsonPlusSerializer.dumps = JsonPlusSerializer.dumps_typed
if not hasattr(JsonPlusSerializer, "loads"):
    JsonPlusSerializer.loads = JsonPlusSerializer.loads_typed


class AgentCheckPointer: 
    def __init__(self): 
        self.mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_memory = None 

    def getMongoDBCheckPointer(self): 
        if self.mongodb_memory is not None:
            return self.mongodb_memory 
        
        sync_client = MongoClient(self.mongo_uri)
        self.mongodb_memory = MongoDBSaver(sync_client)
        return self.mongodb_memory 


checkPointer = AgentCheckPointer()
