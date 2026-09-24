import time
import logging
from fastapi import APIRouter
from app.config import get_settings
from app.schemas import PageIndexRequest, PageIndexResponse
from app.errors import (
    err_text_too_short,
    err_payload_too_large,
    map_llm_exception
)
from app.services.chunking import chunk_text
from app.services.models import get_embeddings
from app.services.page_store import (
    compute_page_id,
    get_page_store,
    PageIndex
)
from langchain_core.vectorstores import InMemoryVectorStore

logger = logging.getLogger("bpe.pages")
router = APIRouter(prefix="/api/v1/pages", tags=["pages"])


@router.post("/index", response_model=PageIndexResponse)
async def index_page(payload: PageIndexRequest):
    settings = get_settings()
    store = get_page_store()

    # Check minimum text length
    if len(payload.text.strip()) < settings.MIN_TEXT_CHARS:
        raise err_text_too_short()

    # Check hard maximum limit (> 2x MAX_TEXT_CHARS)
    if len(payload.text) > settings.MAX_TEXT_CHARS * 2:
        raise err_payload_too_large(
            f"Page text length ({len(payload.text)}) exceeds allowed limit ({settings.MAX_TEXT_CHARS * 2})"
        )

    # Truncate text if exceeds MAX_TEXT_CHARS
    text = payload.text
    was_truncated = payload.truncated
    if len(text) > settings.MAX_TEXT_CHARS:
        text = text[:settings.MAX_TEXT_CHARS]
        was_truncated = True

    page_id = compute_page_id(payload.url, text)

    # 1. Fast cache check
    cached_index = store.get(page_id)
    if cached_index is not None:
        logger.info(f"Page index hit for page_id={page_id}")
        return PageIndexResponse(
            page_id=page_id,
            title=cached_index.title,
            char_count=cached_index.char_count,
            chunk_count=cached_index.chunk_count,
            truncated=cached_index.truncated,
            cached=True
        )

    # 2. Acquire per-page lock to prevent redundant indexing
    lock = store.get_lock(page_id)
    async with lock:
        # Double check after acquiring lock
        cached_index = store.get(page_id)
        if cached_index is not None:
            return PageIndexResponse(
                page_id=page_id,
                title=cached_index.title,
                char_count=cached_index.char_count,
                chunk_count=cached_index.chunk_count,
                truncated=cached_index.truncated,
                cached=True
            )

        # Chunk the text
        chunks, chunks_truncated = chunk_text(text, page_id=page_id, title=payload.title)
        was_truncated = was_truncated or chunks_truncated

        # Generate embeddings and initialize vector store in safe sub-batches
        try:
            embeddings = get_embeddings()
            vector_store = InMemoryVectorStore(embedding=embeddings)
            if chunks:
                BATCH_SIZE = 25
                for i in range(0, len(chunks), BATCH_SIZE):
                    sub_batch = chunks[i:i + BATCH_SIZE]
                    try:
                        await vector_store.aadd_documents(sub_batch)
                    except Exception as sub_err:
                        err_str = str(sub_err).lower()
                        # If rate limited after some chunks are indexed, keep partial index
                        if len(vector_store.store) > 0 and ("429" in err_str or "resourceexhausted" in err_str or "quota" in err_str):
                            logger.warning(
                                f"Hit rate limit after indexing {len(vector_store.store)} chunks for page_id={page_id}. Proceeding with partial index."
                            )
                            was_truncated = True
                            chunks = chunks[:len(vector_store.store)]
                            break
                        raise sub_err
        except Exception as e:
            logger.error(f"Error embedding chunks for page_id={page_id}: {e}")
            raise map_llm_exception(e)

        index_entry = PageIndex(
            page_id=page_id,
            url=payload.url,
            title=payload.title,
            text=text,
            char_count=len(text),
            chunk_count=len(chunks),
            truncated=was_truncated,
            vector_store=vector_store,
            created_at=time.time(),
            last_used=time.time()
        )
        store.put(index_entry)

        logger.info(f"Successfully indexed page_id={page_id}, chunks={len(chunks)}, chars={len(text)}")
        return PageIndexResponse(
            page_id=page_id,
            title=payload.title,
            char_count=len(text),
            chunk_count=len(chunks),
            truncated=was_truncated,
            cached=False
        )
