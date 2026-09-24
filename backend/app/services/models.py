from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.config import get_settings
from app.errors import err_invalid_api_key


def get_embeddings():
    """Return embedding model instance, or raise AppError if key is missing."""
    settings = get_settings()
    if not settings.is_llm_configured:
        raise err_invalid_api_key("Gemini API key is not configured")

    kwargs = {
        "model": settings.GEMINI_EMBEDDING_MODEL,
        "google_api_key": settings.GOOGLE_API_KEY,
    }
    if settings.EMBEDDING_DIMENSIONS:
        kwargs["output_dimensionality"] = settings.EMBEDDING_DIMENSIONS

    return GoogleGenerativeAIEmbeddings(**kwargs)


def get_llm(temperature: Optional[float] = None, streaming: bool = True):
    """Return chat LLM instance, or raise AppError if key is missing."""
    settings = get_settings()
    if not settings.is_llm_configured:
        raise err_invalid_api_key("Gemini API key is not configured")

    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temp,
        streaming=streaming,
    )
