import os
from pinecone import Pinecone

class VectorDBClientFactory:
   
    
    _instance = Pinecone

    @classmethod
    def get_client(cls, index_name=None):
       
       
        if cls._instance is None:
            api_key = os.getenv("vector_database_url")
            index_name = index_name 
            cls._instance =  Pinecone(api_key=api_key)
            
        else:
            raise ValueError(f"Error in connecting with the Vector Database")
        
        return cls._instance


vectorDB = VectorDBClientFactory() 


