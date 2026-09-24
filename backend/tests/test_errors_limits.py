import time
import pytest
from httpx import AsyncClient
from app.config import get_settings
from app.errors import map_llm_exception, err_page_not_found
from app.ratelimit import get_rate_limiter
from app.services.page_store import get_page_store, PageIndex
from langchain_core.vectorstores import InMemoryVectorStore


def test_map_llm_exception():
    # 1. Quota
    class ResourceExhaustedError(Exception):
        pass
    quota_err = map_llm_exception(ResourceExhaustedError("429 Quota exceeded for model"))
    assert quota_err.code == "LLM_QUOTA_EXCEEDED"
    assert quota_err.http_status == 429

    # 2. Invalid Key
    class PermissionDenied(Exception):
        pass
    key_err = map_llm_exception(PermissionDenied("API key not valid. Please pass a valid API key."))
    assert key_err.code == "INVALID_API_KEY"
    assert key_err.http_status == 500

    # 3. Timeout
    timeout_err = map_llm_exception(TimeoutError("Request timed out after 90 seconds"))
    assert timeout_err.code == "LLM_UNAVAILABLE"
    assert timeout_err.http_status == 502

    # 4. Embedding
    embed_err = map_llm_exception(Exception("Failed generating embedding vectors"))
    assert embed_err.code == "EMBEDDING_FAILED"
    assert embed_err.http_status == 502


@pytest.mark.asyncio
async def test_rate_limiting(monkeypatch, async_client: AsyncClient):
    settings = get_settings()
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 3)
    get_rate_limiter().reset()

    # Make 3 allowed requests
    for i in range(3):
        res = await async_client.post("/api/v1/pages/index", json={})
        assert res.status_code == 422  # validation error but allowed through rate limiter

    # 4th request should be rate limited
    res4 = await async_client.post("/api/v1/pages/index", json={})
    assert res4.status_code == 429
    data = res4.json()
    assert data["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in res4.headers

    # Reset rate limiter
    get_rate_limiter().reset()


@pytest.mark.asyncio
async def test_oversized_question(async_client: AsyncClient):
    store = get_page_store()
    page_id = "test_oversized_q"
    store.put(PageIndex(
        page_id=page_id,
        url="https://example.com/test",
        title="Test",
        text="Sample text",
        char_count=11,
        chunk_count=1,
        truncated=False,
        vector_store=InMemoryVectorStore(embedding=None),
        created_at=time.time(),
        last_used=time.time()
    ))

    # Question > 1000 chars
    res = await async_client.post("/api/v1/chat", json={
        "page_id": page_id,
        "question": "A" * 1001,
        "style": "simple",
        "history": []
    })
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
