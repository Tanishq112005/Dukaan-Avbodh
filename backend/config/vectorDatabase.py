import os
from pinecone import Pinecone

class VectorDBClientFactory:
    _instance = None
    _index = None

    @classmethod
    def get_index(cls, index_name="dukaan-products"):
        if cls._instance is None:
            # os.getenv use kiya gaya hai. .env mein PINECONE_API_KEY zarur add karna
            api_key = os.getenv("PINECONE_API_KEY") 
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable is missing")
            
            cls._instance = Pinecone(api_key=api_key)
            
        if cls._index is None:
            cls._index = cls._instance.Index(index_name)
            
        return cls._index

vectorDB = VectorDBClientFactory()
