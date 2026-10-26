import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from Chat.schemas import ChatRequest, EventRequest, AuthSyncRequest
from agents.user.controller import agentController

logger = logging.getLogger(__name__)

router = APIRouter(tags=["User Agent"])


@router.post("/chat/message")
async def chat_message_endpoint(req: ChatRequest, request: Request):
    """
    Main user chat endpoint.
    Returns full JSON by default. If the client requests streaming
    (via 'Accept: text/event-stream' header or '?stream=true' query parameter),
    streams execution updates and tokens via Server-Sent Events (SSE).
    """
    accept_header = request.headers.get("accept", "")
    is_stream = (
        "text/event-stream" in accept_header
        or request.query_params.get("stream", "").lower() in ("true", "1")
    )

    if is_stream:
        return StreamingResponse(
            agentController.stream_message(req, request=request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await agentController.process_message(req, request=request)


@router.post("/chat/message/stream")
@router.post("/chat/stream")
async def chat_message_stream_endpoint(req: ChatRequest, request: Request):
    """
    Dedicated Server-Sent Events (SSE) streaming endpoint for user chat messages.
    Yields real-time graph node progress, intermediate tool updates, token streams,
    and final structured response payload with authenticated user_id context.
    """
    return StreamingResponse(
        agentController.stream_message(req, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/event")
async def chat_event_endpoint(req: EventRequest, request: Request):
    """
    Handles user events (e.g. login, signup, payment_completed, combo_declined, proactive triggers).
    Streams if 'text/event-stream' is requested; otherwise returns standard JSON.
    """
    accept_header = request.headers.get("accept", "")
    is_stream = (
        "text/event-stream" in accept_header
        or request.query_params.get("stream", "").lower() in ("true", "1")
    )

    if is_stream:
        return StreamingResponse(
            agentController.stream_event(req, request=request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await agentController.process_event(req, request=request)


@router.post("/chat/event/stream")
async def chat_event_stream_endpoint(req: EventRequest, request: Request):
    """
    Dedicated Server-Sent Events (SSE) streaming endpoint for chat events.
    """
    return StreamingResponse(
        agentController.stream_event(req, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/auth-sync")
@router.post("/chat/sync-auth")
async def chat_auth_sync_endpoint(req: AuthSyncRequest, request: Request):
    """
    Explicit endpoint called immediately when user logs in or signs up.
    Extracts the user ID from the access token and injects it directly into
    LangGraph AgentState, Redis cache, and active conversation thread.
    """
    return await agentController.sync_auth_state(
        thread_id=req.thread_id,
        user_id=req.user_id,
        token=req.access_token,
        request=request,
    )
