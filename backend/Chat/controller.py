import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from Chat.database import chat, Chat
from Chat.models import ChatThread, ChatMessage, ThreadState

logger = logging.getLogger(__name__)


class ChatController:
    def __init__(self, chat_db: Optional[Chat] = None):
        self.db = chat_db or chat

    async def get_or_create_thread(self, user_id: int, thread_id: str) -> dict:
        try:
            return await self.db.get_or_create_thread(user_id=user_id, thread_id=thread_id)
        except Exception:
            logger.exception("Failed to get or create chat thread %s for user %s", thread_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get or create chat thread"
            )

    async def add_message(self, user_id: int, thread_id: str, message: ChatMessage):
        try:
            return await self.db.add_message(user_id=user_id, thread_id=thread_id, message=message)
        except Exception:
            logger.exception("Failed to add message to thread %s for user %s", thread_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message"
            )

    async def get_thread(self, user_id: int, thread_id: str):
        try:
            thread = await self.db.get_thread(user_id=user_id, thread_id=thread_id)
            if not thread:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Thread not found"
                )
            return thread
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to get chat thread %s for user %s", thread_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get chat thread"
            )

    async def get_all_threads_for_user(self, user_id: int) -> List[dict]:
        try:
            return await self.db.get_all_threads_for_user(user_id=user_id)
        except Exception:
            logger.exception("Failed to get chat threads for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get chat threads"
            )

    async def update_state(self, user_id: int, thread_id: str, new_state: ThreadState):
        try:
            return await self.db.update_state(user_id=user_id, thread_id=thread_id, new_state=new_state)
        except Exception:
            logger.exception("Failed to update state for thread %s", thread_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update thread state"
            )

    async def update_state_patch(self, user_id: int, thread_id: str, patch: dict):
        try:
            return await self.db.update_state_patch(user_id=user_id, thread_id=thread_id, patch=patch)
        except Exception:
            logger.exception("Failed to patch state for thread %s", thread_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to patch thread state"
            )

    async def append_negotiation_log(self, user_id: int, thread_id: str, log: dict):
        try:
            return await self.db.append_negotiation_log(user_id=user_id, thread_id=thread_id, log=log)
        except Exception:
            logger.exception("Failed to append negotiation log for thread %s", thread_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to append negotiation log"
            )

    async def delete_thread(self, user_id: int, thread_id: str) -> dict:
        try:
            deleted = await self.db.delete_thread(user_id=user_id, thread_id=thread_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Thread not found or already deleted"
                )
            return {"success": True, "message": "Thread deleted successfully"}
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to delete thread %s for user %s", thread_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chat thread"
            )


chatController = ChatController()
