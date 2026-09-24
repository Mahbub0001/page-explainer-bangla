import logging
from fastapi import APIRouter, Request
from app.schemas import ChatRequest, SummarizeRequest, ExplainSelectionRequest
from app.errors import err_page_not_found, err_validation, err_payload_too_large
from app.services.page_store import get_page_store
from app.services.rag import stream_chat_response, stream_explain_response
from app.services.summarize import stream_summary_response
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
        raise err_payload_too_large("Question exceeds 1,000 characters limit")
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


@router.post("/summarize")
async def summarize_endpoint(payload: SummarizeRequest, request: Request):
    # Pre-stream validation: check if page exists
    store = get_page_store()
    page_index = store.get(payload.page_id)
    if not page_index:
        raise err_page_not_found()

    generator = stream_summary_response(
        page_id=payload.page_id,
        style=payload.style,
        request=request
    )

    return create_streaming_response(generator)


@router.post("/explain-selection")
async def explain_selection_endpoint(payload: ExplainSelectionRequest, request: Request):
    # Pre-stream validation: check if page exists
    store = get_page_store()
    page_index = store.get(payload.page_id)
    if not page_index:
        raise err_page_not_found()

    if len(payload.selection) > 4000:
        raise err_payload_too_large("Selected text exceeds 4,000 characters limit")

    generator = stream_explain_response(
        page_id=payload.page_id,
        selection=payload.selection,
        style=payload.style,
        request=request
    )

    return create_streaming_response(generator)

