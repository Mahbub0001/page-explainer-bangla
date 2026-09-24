import logging
from fastapi import APIRouter, Request
from app.schemas import ChatRequest
from app.errors import err_page_not_found, err_validation
from app.services.page_store import get_page_store
from app.services.rag import stream_chat_response
from app.services.streaming import create_streaming_response

logger = logging.getLogger("bpe.ai")
router = APIRouter(prefix="/api/v1", tags=["ai"])


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest, request: Request):
    # Pre-stream validation: check if page exists
    store = get_page_store()
    page_index = store.get(payload.page_id)
    if not page_index:
        raise err_page_not_found()

    # Pre-stream validation: question and history limits
    if len(payload.question) > 1000:
        raise err_validation("Question exceeds 1,000 characters limit")
    if len(payload.history) > 8:
        raise err_validation("History exceeds maximum of 8 messages")
    for msg in payload.history:
        if len(msg.content) > 2000:
            raise err_validation("Message in history exceeds 2,000 characters limit")

    generator = stream_chat_response(
        page_id=payload.page_id,
        question=payload.question,
        style=payload.style,
        history=payload.history,
        request=request
    )

    return create_streaming_response(generator)
