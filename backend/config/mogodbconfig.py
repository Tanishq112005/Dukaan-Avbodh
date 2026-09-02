import os
from typing import Optional
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

class NoSqlClient:
 
    
    def __init__(self):
        self.uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        self._client: Optional[AsyncMongoClient] = None

    def _connect(self):
        try:
            self._client = AsyncMongoClient(self.uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            raise e

    def get_client(self) -> AsyncMongoClient:
        """Returns the raw AsyncMongoClient instance."""
        if self._client is None:
            self._connect()
        return self._client

    def get_database(self, db_name: str) -> AsyncDatabase:
        """Returns a specific MongoDB database."""
        client = self.get_client()
        return client[db_name]

    def get_collection(self, db_name: str, collection_name: str) -> AsyncCollection:
        """Returns a specific MongoDB collection from a specific database."""
        db = self.get_database(db_name)
        return db[collection_name]

    def close(self):
        """Closes the MongoDB connection."""
        if self._client:
            self._client.close()

nosql_client = NoSqlClient() 