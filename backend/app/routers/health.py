from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", methods=["GET", "HEAD"])
async def health_check():
    settings = get_settings()
    
    # Try getting page store count if initialized
    cached_count = 0
    try:
        from app.services.page_store import get_page_store
        cached_count = get_page_store().count()
    except Exception:
        cached_count = 0

    return {
        "status": "ok",
        "version": "0.1.0",
        "llm_configured": settings.is_llm_configured,
        "chat_model": settings.GEMINI_CHAT_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        "cached_pages": cached_count,
    }
