from fastapi import APIRouter
from typing import List, Dict, Any
from Chat.controller import chatController
from Chat.models import ChatMessage, ThreadState
from Chat.schemas import (
    CreateThreadRequest,
    AddMessageRequest,
    UpdateStatePatchRequest,
    AppendNegotiationLogRequest,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/thread")
async def get_or_create_thread(req: CreateThreadRequest):
    """Fetch an existing thread or initialize a new one for the user."""
    return await chatController.get_or_create_thread(user_id=req.user_id, thread_id=req.thread_id)


@router.get("/thread/{user_id}/{thread_id}")
async def get_thread(user_id: int, thread_id: str):
    """Retrieve details and audit logs for a specific chat thread."""
    return await chatController.get_thread(user_id=user_id, thread_id=thread_id)


@router.get("/threads/{user_id}")
async def get_all_threads_for_user(user_id: int):
    """Retrieve all chat threads belonging to a specific user."""
    return await chatController.get_all_threads_for_user(user_id=user_id)


@router.post("/thread/{thread_id}/message")
async def add_message(thread_id: str, req: AddMessageRequest):
    """Append a chat message to an existing thread."""
    msg = ChatMessage(sender=req.sender, message=req.message, metadata=req.metadata)
    return await chatController.add_message(user_id=req.user_id, thread_id=thread_id, message=msg)


@router.patch("/thread/{thread_id}/state")
async def update_state_patch(thread_id: str, req: UpdateStatePatchRequest):
    """Partially update state values (e.g. current discount, combo offer) in a thread."""
    return await chatController.update_state_patch(user_id=req.user_id, thread_id=thread_id, patch=req.patch)


@router.post("/thread/{thread_id}/negotiation-log")
async def append_negotiation_log(thread_id: str, req: AppendNegotiationLogRequest):
    """Record a negotiation event log in the thread state."""
    return await chatController.append_negotiation_log(user_id=req.user_id, thread_id=thread_id, log=req.log)


@router.delete("/thread/{user_id}/{thread_id}")
async def delete_thread(user_id: int, thread_id: str):
    """Delete a chat thread by user ID and thread ID."""
    return await chatController.delete_thread(user_id=user_id, thread_id=thread_id)
