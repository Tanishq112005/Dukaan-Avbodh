import logging
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse

from middleware.merchant_middleware import require_role
from User.models import UserRole
from Merchant.schemas import MerchantChatRequest, MerchantChatResponse
from agents.merchant.controller import merchantAgentController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merchant/chat", tags=["Merchant Agent"])


@router.post("", response_model=MerchantChatResponse)
@router.post("/message", response_model=MerchantChatResponse)
async def chat_message_endpoint(
    req: MerchantChatRequest,
    request: Request,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """
    Main merchant chat endpoint.
    Returns full JSON by default. If the client requests streaming
    (via 'Accept: text/event-stream' header or '?stream=true' query parameter),
    streams execution updates, tool notifications, and tokens via Server-Sent Events (SSE).
    """
    accept_header = request.headers.get("accept", "")
    is_stream = (
        "text/event-stream" in accept_header
        or request.query_params.get("stream", "").lower() in ("true", "1")
    )

    if is_stream:
        return StreamingResponse(
            merchantAgentController.stream_message(req, current_user=current_user, request=request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await merchantAgentController.process_message(
        req, current_user=current_user, request=request
    )


@router.post("/stream")
@router.post("/message/stream")
async def chat_stream_endpoint(
    req: MerchantChatRequest,
    request: Request,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """
    Dedicated Server-Sent Events (SSE) streaming endpoint for merchant chat messages.
    Yields real-time graph node progress, intermediate tool calls, token streams (with thought suppression),
    and final structured response payload with Generative UI cards.
    """
    return StreamingResponse(
        merchantAgentController.stream_message(req, current_user=current_user, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/threads")
async def get_merchant_chat_threads_endpoint(
    limit: int = 50,
    current_user: dict = Depends(require_role(UserRole.MERCHANT)),
):
    """Retrieves conversation sessions and state snapshots stored in MongoDB 'merchant_chats'."""
    merchant_id = current_user.get("user_id")
    threads = await merchantAgentController.chat_repo.get_merchant_threads(merchant_id=merchant_id, limit=limit)
    return {"threads": threads}
