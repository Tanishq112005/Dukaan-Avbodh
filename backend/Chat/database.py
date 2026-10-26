import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from config.mogodbconfig import nosql_client
from Chat.models import ChatThread, ChatMessage, ThreadState

logger = logging.getLogger(__name__)


class Chat:

    def __init__(self, noSql_collection=None):
        self.db = (
            noSql_collection
            if noSql_collection is not None
            else nosql_client.get_collection("dukaan_audit", "chat_threads")
        )
        self.collection = self.db

    ## Get or create a chat thread for a user
    async def getOrCreateThread(self, user_id: int, thread_id: str) -> dict:
        """Fetch a thread by user_id and thread_id, or create if it doesn't exist."""
        try:
            thread = await self.db.find_one({"user_id": user_id, "thread_id": thread_id})
            if not thread:
                new_thread = ChatThread(user_id=user_id, thread_id=thread_id)
                thread_dict = new_thread.model_dump()
                await self.db.insert_one(thread_dict)
                return thread_dict
            return thread
        except Exception as e:
            logger.warning("Could not get or create thread in Mongo: %s", e)
            return {"user_id": user_id, "thread_id": thread_id, "messages": [], "state": {}}

    get_or_create_thread = getOrCreateThread

    ## Add the Message to the thread 
    async def addMessage(self, user_id: int, thread_id: str, message: ChatMessage):
        """Append a message to a specific thread."""
        try:
            await self.db.update_one(
                {"user_id": user_id, "thread_id": thread_id},
                {
                    "$push": {"messages": message.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )
        except Exception as e:
            logger.warning("Could not add message to MongoDB thread: %s", e)

    add_message = addMessage

    ## Update the state of the thread 
    async def updateState(self, user_id: int, thread_id: str, new_state: ThreadState):
        """Update the agent state (discount, suggested products) for the thread."""
        try:
            await self.db.update_one(
                {"user_id": user_id, "thread_id": thread_id},
                {
                    "$set": {
                        "state": new_state.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.warning("Could not update state in MongoDB thread: %s", e)

    update_state = updateState

    ## Update the state of the thread with a patch (partial update)
    async def updateStatePatch(self, user_id: int, thread_id: str, patch: dict):
        """Partially update the thread state (e.g. state.order_placed)."""
        try:
            set_dict = {"updated_at": datetime.utcnow()}
            for k, v in patch.items():
                set_dict[f"state.{k}"] = v

            await self.db.update_one(
                {"user_id": user_id, "thread_id": thread_id},
                {
                    "$set": set_dict
                },
                upsert=True
            )
        except Exception as e:
            logger.warning("Could not update state patch in MongoDB thread: %s", e)

    update_state_patch = updateStatePatch

    ## Append the negotiation log to the thread state
    async def appendNegotiationLog(self, user_id: int, thread_id: str, log: dict):
        """Append a negotiation round to state.negotiation_log"""
        try:
            log["timestamp"] = datetime.utcnow()
            await self.db.update_one(
                {"user_id": user_id, "thread_id": thread_id},
                {
                    "$push": {"state.negotiation_log": log},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )
        except Exception as e:
            logger.warning("Could not append negotiation log in MongoDB thread: %s", e)

    append_negotiation_log = appendNegotiationLog

    ## Save full turn with human and AI message and state patch atomically
    async def save_full_thread_turn(
        self,
        user_id: int,
        thread_id: str,
        human_text: Optional[str] = None,
        ai_text: Optional[str] = None,
        cards: Optional[List[Dict[str, Any]]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        state_patch: Optional[Dict[str, Any]] = None,
    ):
        """
        Persists conversational turns (human message and AI reply with any executed tool calls and cards)
        and merges state into MongoDB thread for auditability and merchant inspection.
        """
        try:
            now = datetime.utcnow()
            new_msgs = []
            if human_text:
                new_msgs.append({
                    "sender": "human",
                    "message": str(human_text),
                    "tool_calls": None,
                    "cards": None,
                    "timestamp": now,
                })
            if ai_text:
                new_msgs.append({
                    "sender": "ai",
                    "message": str(ai_text),
                    "tool_calls": tool_calls or None,
                    "cards": cards or None,
                    "timestamp": now,
                })

            update_doc: Dict[str, Any] = {
                "$set": {
                    "updated_at": now,
                    "user_id": user_id,
                    "thread_id": thread_id,
                },
                "$setOnInsert": {
                    "created_at": now,
                }
            }

            if new_msgs:
                update_doc["$push"] = {"messages": {"$each": new_msgs}}

            if state_patch:
                for k, v in state_patch.items():
                    update_doc["$set"][f"state.{k}"] = v

            await self.db.update_one(
                {"user_id": user_id, "thread_id": thread_id},
                update_doc,
                upsert=True
            )
        except Exception as e:
            logger.warning("save_full_thread_turn failed for thread %s: %s", thread_id, e)

    ## Get all threads for a user (useful for merchant dashboard)
    async def getAllThreadsForUser(self, user_id: int):
        """Retrieve all chat threads for a user (useful for merchant dashboard)."""
        try:
            cursor = self.db.find({"user_id": user_id}).sort("updated_at", -1)
            threads = await cursor.to_list(length=100)
            for t in threads:
                t["_id"] = str(t["_id"])
            return threads
        except Exception as e:
            logger.warning("Could not get threads for user from MongoDB: %s", e)
            return []

    get_all_threads_for_user = getAllThreadsForUser

    ## Get a specific thread for a user
    async def getThread(self, user_id: int, thread_id: str):
        """Retrieve a specific chat thread."""
        try:
            thread = await self.db.find_one({"user_id": user_id, "thread_id": thread_id})
            if thread:
                thread["_id"] = str(thread["_id"])
            return thread
        except Exception as e:
            logger.warning("Could not get thread from MongoDB: %s", e)
            return None

    get_thread = getThread

    ## Delete a specific thread for a user
    async def deleteThread(self, user_id: int, thread_id: str) -> bool:
        """Delete a specific chat thread."""
        try:
            result = await self.db.delete_one({"user_id": user_id, "thread_id": thread_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.warning("Could not delete thread from MongoDB: %s", e)
            return False

    delete_thread = deleteThread


# Singleton instances
chat = Chat(noSql_collection=nosql_client.get_collection("dukaan_audit", "chat_threads"))
chat_audit_repo = chat
chatRepository = chat
chat_db = chat
ChatDatabase = Chat
ChatRepository = Chat
