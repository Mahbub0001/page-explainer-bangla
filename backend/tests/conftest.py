import pytest
from httpx import AsyncClient, ASGITransport
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from app.main import create_app
from app.config import get_settings


@pytest.fixture
def fake_embeddings():
    return DeterministicFakeEmbedding(size=64)


@pytest.fixture
def fake_chat_model():
    return FakeListChatModel(
        responses=[
            "এই পেজে বলা হয়েছে কৃত্রিম বুদ্ধিমত্তা মানুষের সহায়ক। [1]",
            "সারসংক্ষেপ: পেজটি আধুনিক প্রযুক্তি নিয়ে লেখা।",
            "এই পেজে এর উত্তর পাওয়া যায়নি।"
        ]
    )


@pytest.fixture
async def async_client():
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
