import logging
from fastapi import APIRouter
from app.schemas import PageIndexRequest, PageIndexResponse
from app.errors import err_text_too_short, err_payload_too_large

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pages", tags=["pages"])


@router.post("/index", response_model=PageIndexResponse)
async def index_page(payload: PageIndexRequest):
    # Full implementation in Phase 2
    from app.config import get_settings
    settings = get_settings()

    if len(payload.text) < settings.MIN_TEXT_CHARS:
        raise err_text_too_short()
    
    if len(payload.text) > settings.MAX_TEXT_CHARS * 2:
        raise err_payload_too_large("Page text exceeds double the maximum limit")

    # Placeholder for Phase 1 skeleton
    return PageIndexResponse(
        page_id="test_placeholder",
        title=payload.title,
        char_count=len(payload.text),
        chunk_count=1,
        truncated=payload.truncated,
        cached=False
    )
