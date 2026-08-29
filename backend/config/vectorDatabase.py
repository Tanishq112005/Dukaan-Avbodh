import os
from pinecone import Pinecone, ServerlessSpec

class DummyIndex:
    def query(self, *args, **kwargs):
        class DummyResponse:
            matches = []
        return DummyResponse()
        
    def upsert(self, *args, **kwargs):
        pass

class VectorDBClientFactory:
    _instance = None
    _index = None

    @classmethod
    def get_index(cls, index_name="dukaan-products"):
        if cls._index is not None:
            return cls._index
            
        api_key = os.getenv("PINECONE_API_KEY") 
        if not api_key or api_key == "your_pinecone_api_key_here":
            print("Warning: PINECONE_API_KEY is missing or invalid. Using Dummy VectorDB.")
            cls._index = DummyIndex()
            return cls._index

        if cls._instance is None:
            cls._instance = Pinecone(api_key=api_key)
            
        try:
            # Check if index exists
            existing_indexes = [info["name"] for info in cls._instance.list_indexes()]
            if index_name not in existing_indexes:
                print(f"Creating Pinecone index '{index_name}'...")
                cls._instance.create_index(
                    name=index_name,
                    dimension=384, # sentence-transformers/all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
            cls._index = cls._instance.Index(index_name)
        except Exception as e:
            print(f"Pinecone Error: {e}. Using Dummy VectorDB fallback.")
            cls._index = DummyIndex()
            
        return cls._index

vectorDB = VectorDBClientFactory()
