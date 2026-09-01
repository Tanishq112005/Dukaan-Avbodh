import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

class NoSqlClient:
 
    
    def __init__(self):
        # You can pass the URI directly, or it will fallback to environment variables
        self.uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        self._client: Optional[AsyncIOMotorClient] = None
        self._connect()

    def _connect(self):
        try:
            self._client = AsyncIOMotorClient(self.uri)
            # Motor doesn't block on connection, but we can verify it later if needed
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            raise e

    def get_client(self) -> AsyncIOMotorClient:
        """Returns the raw AsyncIOMotorClient instance."""
        if self._client is None:
            self._connect()
        return self._client

    def get_database(self, db_name: str) -> AsyncIOMotorDatabase:
        """Returns a specific MongoDB database."""
        client = self.get_client()
        return client[db_name]

    def get_collection(self, db_name: str, collection_name: str) -> AsyncIOMotorCollection:
        """Returns a specific MongoDB collection from a specific database."""
        db = self.get_database(db_name)
        return db[collection_name]

    def close(self):
        """Closes the MongoDB connection."""
        if self._client:
            self._client.close()
