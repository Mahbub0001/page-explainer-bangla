import pytest
import asyncio
from httpx import AsyncClient
from app.services.page_store import get_page_store


@pytest.mark.asyncio
async def test_index_page_happy_path(monkeypatch, fake_embeddings, async_client: AsyncClient):
    # Override get_embeddings to use deterministic fake embeddings
    monkeypatch.setattr("app.routers.pages.get_embeddings", lambda: fake_embeddings)
    get_page_store().clear()

    payload = {
        "url": "https://example.com/test-article",
        "title": "Test Article",
        "text": (
            "Artificial intelligence is transforming how people read and process information across multiple languages. "
            "Bengali or Bangla is one of the most widely spoken languages in the world with over three hundred million speakers. "
            "This application bridges English technical content and Bangla readers seamlessly."
        ),
        "truncated": False,
        "lang": "en"
    }

    # First request: not cached
    res1 = await async_client.post("/api/v1/pages/index", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "page_id" in data1
    assert data1["chunk_count"] > 0
    assert data1["cached"] is False
    assert data1["title"] == "Test Article"

    # Verify lazy state: raw_chunks stored, 0 embeddings generated upfront
    entry = get_page_store().get(data1["page_id"])
    assert entry is not None
    assert len(entry.raw_chunks) > 0
    assert len(entry.embedded_chunk_ids) == 0
    assert len(entry.vector_store.store) == 0

    # Second request: cached
    res2 = await async_client.post("/api/v1/pages/index", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["page_id"] == data1["page_id"]
    assert data2["cached"] is True



@pytest.mark.asyncio
async def test_index_page_too_short(async_client: AsyncClient):
    payload = {
        "url": "https://example.com/short",
        "title": "Short",
        "text": "Too short text.",
        "truncated": False,
        "lang": "en"
    }
    res = await async_client.post("/api/v1/pages/index", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "TEXT_TOO_SHORT"


@pytest.mark.asyncio
async def test_index_page_oversized(async_client: AsyncClient):
    payload = {
        "url": "https://example.com/huge",
        "title": "Huge",
        "text": "A" * 250000,
        "truncated": False,
        "lang": "en"
    }
    res = await async_client.post("/api/v1/pages/index", json=payload)
    assert res.status_code == 413
    data = res.json()
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_concurrent_index_requests(monkeypatch, fake_embeddings, async_client: AsyncClient):
    monkeypatch.setattr("app.routers.pages.get_embeddings", lambda: fake_embeddings)
    get_page_store().clear()

    payload = {
        "url": "https://example.com/concurrent",
        "title": "Concurrent",
        "text": "This is a meaningful article body that has more than one hundred characters of content to satisfy the length test requirement easily." * 2,
        "truncated": False,
        "lang": "en"
    }

    # Fire 3 concurrent index requests
    res1, res2, res3 = await asyncio.gather(
        async_client.post("/api/v1/pages/index", json=payload),
        async_client.post("/api/v1/pages/index", json=payload),
        async_client.post("/api/v1/pages/index", json=payload),
    )
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res3.status_code == 200

    results = [res1.json(), res2.json(), res3.json()]
    page_ids = {r["page_id"] for r in results}
    assert len(page_ids) == 1  # All return the exact same page_id
