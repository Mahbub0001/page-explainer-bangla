import re
import logging
from typing import List, Tuple, Dict, Any, AsyncGenerator
from fastapi import Request
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.documents import Document

from app.config import get_settings
from app.errors import (
    AppError,
    err_page_not_found,
    map_llm_exception
)
from app.schemas import ChatHistoryMessage
from app.services.models import get_llm
from app.services.page_store import get_page_store, PageIndex
from app.services.prompts import (
    build_chat_system_prompt,
    build_rewrite_prompt
)
from app.services.streaming import ndjson, text_from_chunk

logger = logging.getLogger("bpe.rag")


def detect_language_hint(title: str, text: str) -> str:
    """
    Returns 'Bangla' if >30% of alphabetic characters are in the Bengali Unicode range (U+0980-U+09FF),
    otherwise 'English'.
    """
    sample = (title + " " + text[:2000]).strip()
    if not sample:
        return "English"

    # Count Bengali characters and ASCII alphabetic characters
    bengali_chars = len(re.findall(r"[\u0980-\u09FF]", sample))
    latin_chars = len(re.findall(r"[a-zA-Z]", sample))
    total_letters = bengali_chars + latin_chars

    if total_letters > 0 and (bengali_chars / total_letters) > 0.30:
        return "Bangla"
    return "English"


async def rewrite_query(
    question: str,
    history: List[ChatHistoryMessage],
    lang_hint: str
) -> str:
    """
    Rewrite a follow-up question and history into a standalone search query.
    Falls back to original question on failure.
    """
    if not history:
        return question

    try:
        llm = get_llm(temperature=0.0, streaming=False)
        system_instruction = build_rewrite_prompt(lang_hint)

        messages = [SystemMessage(content=system_instruction)]
        for msg in history[-4:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=question))

        response = await llm.ainvoke(messages)
        rewritten = text_from_chunk(response).strip()
        # Clean quotes or newlines
        first_line = rewritten.split("\n")[0].strip().strip('"').strip("'")
        if first_line:
            logger.info(f"Rewrote query '{question}' -> '{first_line}'")
            return first_line
    except Exception as e:
        logger.warning(f"Query rewrite failed, falling back to raw question: {e}")

    return question


async def retrieve_context(
    page_index: PageIndex,
    query: str,
    k: int = 5
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieve top-k chunks plus lead chunk (chunk_id=0).
    Returns formatted context string and sources payload.
    """
    vs = page_index.vector_store
    results: List[Tuple[Document, float]] = []

    try:
        # Search vector store with score
        results = await vs.asimilarity_search_with_score(query, k=k)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        # If search fails, retrieve first few documents as fallback
        docs_dict = list(vs.store.values())[:k]
        for d in docs_dict:
            doc = Document(page_content=d["text"], metadata=d["metadata"])
            results.append((doc, 0.5))

    # Retrieve lead chunk (chunk_id == 0)
    lead_doc = None
    for item in vs.store.values():
        if item.get("metadata", {}).get("chunk_id") == 0:
            lead_doc = Document(page_content=item["text"], metadata=item["metadata"])
            break

    # Combine unique documents by chunk_id
    seen_chunk_ids = set()
    selected_docs: List[Tuple[Document, float]] = []

    # Include lead doc first if available
    if lead_doc:
        lead_id = lead_doc.metadata.get("chunk_id", 0)
        seen_chunk_ids.add(lead_id)
        selected_docs.append((lead_doc, 1.0))

    for doc, score in results:
        cid = doc.metadata.get("chunk_id")
        if cid not in seen_chunk_ids:
            seen_chunk_ids.add(cid)
            selected_docs.append((doc, float(score)))

    # Sort selected documents by chunk_id for sequential context flow
    selected_docs.sort(key=lambda x: x[0].metadata.get("chunk_id", 0))

    # Build context and sources payload
    context_lines = [
        f"PAGE TITLE: {page_index.title}",
        f"PAGE URL: {page_index.url}"
    ]
    sources = []

    for idx, (doc, score) in enumerate(selected_docs, start=1):
        context_lines.append(f"[{idx}] {doc.page_content}")
        # Snippet for source UI capped at 400 chars
        snippet = doc.page_content[:400].strip()
        sources.append({
            "id": idx,
            "chunk_id": doc.metadata.get("chunk_id", 0),
            "text": snippet,
            "score": round(float(score), 3)
        })

    formatted_context = "\n".join(context_lines)
    return formatted_context, sources


async def stream_chat_response(
    page_id: str,
    question: str,
    style: str,
    history: List[ChatHistoryMessage],
    request: Request
) -> AsyncGenerator[bytes, None]:
    """
    Main generator for POST /api/v1/chat streaming.
    Yields:
      1. sources event
      2. token events
      3. done event (or error event)
    """
    store = get_page_store()
    page_index = store.get(page_id)
    if not page_index:
        raise err_page_not_found()

    # Step 1: Query rewrite if history exists
    lang_hint = detect_language_hint(page_index.title, page_index.text)
    search_query = await rewrite_query(question, history, lang_hint)

    # Step 2: Retrieve relevant chunks
    settings = get_settings()
    context, sources = await retrieve_context(page_index, search_query, k=settings.RETRIEVAL_K)

    # Step 3: Emit sources event first
    yield ndjson({"type": "sources", "sources": sources})

    # Step 4: Build prompt & call LLM
    try:
        system_content = build_chat_system_prompt(context, style=style)
        messages = [SystemMessage(content=system_content)]

        # Add up to 8 history messages
        for msg in history[-8:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        # Add original question
        messages.append(HumanMessage(content=question))

        llm = get_llm(streaming=True)

        async for chunk in llm.astream(messages):
            if await request.is_disconnected():
                logger.info("Client disconnected during chat stream")
                return

            text_token = text_from_chunk(chunk)
            if text_token:
                yield ndjson({"type": "token", "text": text_token})

        yield ndjson({"type": "done"})

    except Exception as exc:
        logger.error(f"Error during streaming chat: {exc}")
        app_err = map_llm_exception(exc)
        yield ndjson({
            "type": "error",
            "code": app_err.code,
            "message_bn": app_err.message_bn
        })
