import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "llm_configured" in data
    assert "chat_model" in data
    assert "embedding_model" in data
    assert "cached_pages" in data


@pytest.mark.asyncio
async def test_health_without_key(monkeypatch, async_client: AsyncClient):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "")
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["llm_configured"] is False


@pytest.mark.asyncio
async def test_validation_error_shape(async_client: AsyncClient):
    response = await async_client.post("/api/v1/pages/index", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in data["error"]
    assert "message_bn" in data["error"]
    assert "অনুরোধের তথ্য সঠিক নয়" in data["error"]["message_bn"]

