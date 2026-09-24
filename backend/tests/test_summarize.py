import json
import time
import pytest
from httpx import AsyncClient
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from app.config import get_settings
from app.services.page_store import get_page_store, PageIndex


@pytest.fixture
def test_page_index(fake_embeddings):
    get_page_store().clear()
    vs = InMemoryVectorStore(embedding=fake_embeddings)
    doc1 = Document(
        page_content="Deep learning uses artificial neural networks with representation learning.",
        metadata={"chunk_id": 0, "title": "Deep Learning"}
    )
    doc2 = Document(
        page_content="Backpropagation computes gradients of the loss function effectively.",
        metadata={"chunk_id": 1, "title": "Deep Learning"}
    )
    vs.add_documents([doc1, doc2])

    page_id = "summary_test_page"
    page = PageIndex(
        page_id=page_id,
        url="https://example.com/deep-learning",
        title="Deep Learning",
        text=(
            "Deep learning uses artificial neural networks with representation learning. "
            "It has revolutionized computer vision and speech recognition.\n\n"
            "Backpropagation computes gradients of the loss function effectively. "
            "Optimizers like Adam adjust network weights based on these gradients."
        ),
        char_count=240,
        chunk_count=2,
        truncated=False,
        vector_store=vs,
        created_at=time.time(),
        last_used=time.time()
    )
    get_page_store().put(page)
    return page


@pytest.mark.asyncio
async def test_summarize_stuff_path(test_page_index, monkeypatch, fake_chat_model, async_client: AsyncClient):
    monkeypatch.setattr("app.services.summarize.get_llm", lambda *a, **kw: fake_chat_model)

    res = await async_client.post("/api/v1/summarize", json={
        "page_id": test_page_index.page_id,
        "style": "simple"
    })
    assert res.status_code == 200
    assert "application/x-ndjson" in res.headers["content-type"]

    lines = [l.strip() for l in res.text.split("\n") if l.strip()]
    events = [json.loads(l) for l in lines]

    # First event is empty sources
    assert events[0]["type"] == "sources"
    assert events[0]["sources"] == []

    # Intermediate events are tokens
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0

    # Last event is done
    assert events[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_summarize_map_reduce_path(test_page_index, monkeypatch, fake_chat_model, async_client: AsyncClient):
    monkeypatch.setattr("app.services.summarize.get_llm", lambda *a, **kw: fake_chat_model)
    settings = get_settings()
    # Force map-reduce by setting tiny STUFF_LIMIT_CHARS and tiny MAP_CHUNK_CHARS
    monkeypatch.setattr(settings, "STUFF_LIMIT_CHARS", 50)
    monkeypatch.setattr(settings, "MAP_CHUNK_CHARS", 100)

    res = await async_client.post("/api/v1/summarize", json={
        "page_id": test_page_index.page_id,
        "style": "simple"
    })
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.strip()]
    events = [json.loads(l) for l in lines]

    assert events[0]["type"] == "sources"
    assert events[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_explain_selection_stream_order(test_page_index, monkeypatch, fake_chat_model, async_client: AsyncClient):
    monkeypatch.setattr("app.services.rag.get_llm", lambda *a, **kw: fake_chat_model)

    res = await async_client.post("/api/v1/explain-selection", json={
        "page_id": test_page_index.page_id,
        "selection": "Backpropagation computes gradients",
        "style": "simple"
    })
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.strip()]
    events = [json.loads(l) for l in lines]

    # First event has sources
    assert events[0]["type"] == "sources"
    assert len(events[0]["sources"]) > 0

    # Tokens and done
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0
    assert events[-1]["type"] == "done"


@pytest.mark.asyncio
async def test_explain_selection_oversized(test_page_index, async_client: AsyncClient):
    huge_selection = "A" * 4001
    res = await async_client.post("/api/v1/explain-selection", json={
        "page_id": test_page_index.page_id,
        "selection": huge_selection,
        "style": "simple"
    })
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
