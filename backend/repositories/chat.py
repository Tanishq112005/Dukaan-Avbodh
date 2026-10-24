from config.mogodbconfig import NoSqlClient
from models.chat_audit import ChatThread, ChatMessage, ThreadState
from datetime import datetime
from config.mogodbconfig import nosql_client  


  
class Chat:
    
    def __init__(self , noSql_client):
        self.client = noSql_client
        self.db = self.client.get_collection("dukaan_audit", "chat_threads")
        
        

    
    async def get_or_create_thread(self, user_id: int, thread_id: str) -> dict:
        """Fetch a thread by user_id and thread_id, or create if it doesn't exist."""
        thread = await self.db.find_one({"user_id": user_id, "thread_id": thread_id})
        if not thread:
            new_thread = ChatThread(user_id=user_id, thread_id=thread_id)
            thread_dict = new_thread.model_dump()
            await self.db.insert_one(thread_dict)
            return thread_dict
        return thread
    
    ## Add the Message to the thread 
    async def addMessage(self, user_id: int, thread_id: str, message: ChatMessage):
        """Append a message to a specific thread."""
        await self.db.update_one(
            {"user_id": user_id, "thread_id": thread_id},
            {
                "$push": {"messages": message.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    
    ## Update the state of the thread 
    async def updateState(self, user_id: int, thread_id: str, new_state: ThreadState):
        """Update the agent state (discount, suggested products) for the thread."""
        await self.db.update_one(
            {"user_id": user_id, "thread_id": thread_id},
            {
                "$set": {
                    "state": new_state.model_dump(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
     
     
    ## Update the state of the thread with a patch (partial update)
    async def updateStatePatch(self, user_id: int, thread_id: str, patch: dict):
        """Partially update the thread state (e.g. state.order_placed)."""
        set_dict = {"updated_at": datetime.utcnow()}
        for k, v in patch.items():
            set_dict[f"state.{k}"] = v
            
        await self.db.update_one(
            {"user_id": user_id, "thread_id": thread_id},
            {
                "$set": set_dict
            }
        )
    
    
    ## Append the negotiation log to the thread state
    async def appendNegotiationLog(self, user_id: int, thread_id: str, log: dict):
        """Append a negotiation round to state.negotiation_log"""
        log["timestamp"] = datetime.utcnow()
        await self.db.update_one(
            {"user_id": user_id, "thread_id": thread_id},
            {
                "$push": {"state.negotiation_log": log},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
     
    ## Get all threads for a user (useful for merchant dashboard)
    async def getAllThreadsForUser(self, user_id: int):
        """Retrieve all chat threads for a user (useful for merchant dashboard)."""
        cursor = self.db.find({"user_id": user_id}).sort("updated_at", -1)
        threads = await cursor.to_list(length=100)
        
        # Format MongoDB `_id` to string for JSON serialization
        for t in threads:
            t["_id"] = str(t["_id"])
            
        return threads
    
    
    ## Get a specific thread for a user
    async def getThread(self, user_id: int, thread_id: str):
        """Retrieve a specific chat thread."""
        thread = await self.db.find_one({"user_id": user_id, "thread_id": thread_id})
        if thread:
            thread["_id"] = str(thread["_id"])
        return thread



# Singleton instance
chat_audit_repo = Chat(noSql_client=nosql_client)
