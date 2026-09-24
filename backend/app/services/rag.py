import re
import math
import logging
from collections import Counter
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


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase words, supporting Bengali and alphanumeric characters."""
    return [t for t in re.findall(r"[\w\u0980-\u09FF]+", text.lower()) if len(t) > 1]


def select_candidate_chunks(
    raw_chunks: List[Document],
    query: str,
    top_n: int = 12
) -> List[Document]:
    """
    Select top candidate chunks via BM25 keyword overlap.
    Always includes the lead chunk (chunk_id == 0).
    """
    if not raw_chunks:
        return []
    if len(raw_chunks) <= top_n:
        return list(raw_chunks)

    query_tokens = tokenize_text(query)
    if not query_tokens:
        # If query has no extractable terms, return first top_n chunks
        return list(raw_chunks[:top_n])

    chunk_tokens_list = [tokenize_text(doc.page_content) for doc in raw_chunks]
    n_docs = len(raw_chunks)
    avgdl = sum(len(toks) for toks in chunk_tokens_list) / max(n_docs, 1)

    df: Dict[str, int] = {}
    for q in query_tokens:
        df[q] = sum(1 for toks in chunk_tokens_list if q in toks)

    k1 = 1.5
    b = 0.75

    scores: List[Tuple[int, int, float]] = []  # (list_idx, chunk_id, score)
    for idx, (doc, toks) in enumerate(zip(raw_chunks, chunk_tokens_list)):
        doc_len = len(toks)
        tok_counts = Counter(toks)
        score = 0.0
        for q in query_tokens:
            q_df = df.get(q, 0)
            if q_df == 0:
                continue
            idf = math.log((n_docs - q_df + 0.5) / (q_df + 0.5) + 1.0)
            tf = tok_counts[q]
            denom = tf + k1 * (1.0 - b + b * (doc_len / (avgdl or 1.0)))
            score += idf * ((tf * (k1 + 1.0)) / (denom or 1.0))

        cid = doc.metadata.get("chunk_id", idx)
        scores.append((idx, cid, score))

    # Identify lead chunk (chunk_id == 0) index
    lead_idx = 0
    for idx, doc in enumerate(raw_chunks):
        if doc.metadata.get("chunk_id") == 0:
            lead_idx = idx
            break

    # Sort remaining candidates by score descending, then chunk_id ascending
    other_scores = [s for s in scores if s[0] != lead_idx]
    other_scores.sort(key=lambda x: (-x[2], x[1]))

    selected_indices = [lead_idx]
    for idx, cid, score in other_scores:
        if len(selected_indices) >= top_n:
            break
        selected_indices.append(idx)

    # Return candidates sorted by original chunk order
    return [raw_chunks[i] for i in sorted(selected_indices)]


async def retrieve_context(
    page_index: PageIndex,
    query: str,
    k: int = 5
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieve top-k chunks plus lead chunk (chunk_id=0).
    Employs on-demand lazy embedding: selects BM25 candidate chunks,
    embeds only unembedded candidates, and reranks via vector similarity.
    Returns formatted context string and sources payload.
    """
    vs = page_index.vector_store
    candidates: List[Document] = []

    # 1. On-demand lazy embedding of candidate chunks
    if page_index.raw_chunks:
        candidates = select_candidate_chunks(page_index.raw_chunks, query, top_n=12)
        unembedded = [
            c for c in candidates
            if c.metadata.get("chunk_id") not in page_index.embedded_chunk_ids
        ]
        if unembedded:
            store = get_page_store()
            lock = store.get_lock(page_index.page_id)
            async with lock:
                still_unembedded = [
                    c for c in candidates
                    if c.metadata.get("chunk_id") not in page_index.embedded_chunk_ids
                ]
                if still_unembedded:
                    try:
                        logger.info(
                            f"Lazily embedding {len(still_unembedded)} candidate chunks for page_id={page_index.page_id}"
                        )
                        await vs.aadd_documents(still_unembedded)
                        page_index.embedded_chunk_ids.update(
                            c.metadata.get("chunk_id") for c in still_unembedded
                            if "chunk_id" in c.metadata
                        )
                    except Exception as emb_err:
                        logger.error(f"Lazy embedding failed for page_id={page_index.page_id}: {emb_err}")

    # 2. Vector similarity search across embedded chunks
    results: List[Tuple[Document, float]] = []
    try:
        if len(vs.store) > 0:
            results = await vs.asimilarity_search_with_score(query, k=k)
    except Exception as e:
        logger.error(f"Vector search failed: {e}")

    # Fallback if vector search returned nothing
    if not results:
        fallback_docs = candidates[:k] if candidates else (
            page_index.raw_chunks[:k] if page_index.raw_chunks else [
                Document(page_content=d["text"], metadata=d["metadata"])
                for d in list(vs.store.values())[:k]
            ]
        )
        for d in fallback_docs:
            results.append((d, 0.5))

    # 3. Retrieve lead chunk (chunk_id == 0)
    lead_doc = None
    if page_index.raw_chunks:
        for c in page_index.raw_chunks:
            if c.metadata.get("chunk_id") == 0:
                lead_doc = c
                break
    if lead_doc is None:
        for item in vs.store.values():
            if item.get("metadata", {}).get("chunk_id") == 0:
                lead_doc = Document(page_content=item["text"], metadata=item["metadata"])
                break

    # 4. Combine unique documents by chunk_id
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

    # 5. Build context and sources payload
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


async def stream_explain_response(
    page_id: str,
    selection: str,
    style: str,
    request: Request
) -> AsyncGenerator[bytes, None]:
    """
    Main generator for POST /api/v1/explain-selection streaming.
    Yields:
      1. sources event
      2. token events
      3. done event (or error event)
    """
    store = get_page_store()
    page_index = store.get(page_id)
    if not page_index:
        raise err_page_not_found()

    # Search with selection truncated to 500 chars
    search_query = selection[:500].strip()
    settings = get_settings()
    context, sources = await retrieve_context(page_index, search_query, k=settings.RETRIEVAL_K)

    # 1. Emit sources event first
    yield ndjson({"type": "sources", "sources": sources})

    # 2. Build prompt and stream
    try:
        from app.services.prompts import build_explain_prompt
        prompt_text = build_explain_prompt(selection=selection, context=context, style=style)
        messages = [HumanMessage(content=prompt_text)]

        llm = get_llm(streaming=True)
        async for chunk in llm.astream(messages):
            if await request.is_disconnected():
                logger.info("Client disconnected during explain-selection stream")
                return

            text_token = text_from_chunk(chunk)
            if text_token:
                yield ndjson({"type": "token", "text": text_token})

        yield ndjson({"type": "done"})

    except Exception as exc:
        logger.error(f"Error during streaming explain-selection: {exc}")
        app_err = map_llm_exception(exc)
        yield ndjson({
            "type": "error",
            "code": app_err.code,
            "message_bn": app_err.message_bn
        })

