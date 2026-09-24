import asyncio
import logging
from typing import List, AsyncGenerator
from fastapi import Request
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings
from app.errors import (
    err_page_not_found,
    map_llm_exception
)
from app.services.models import get_llm
from app.services.page_store import get_page_store
from app.services.prompts import (
    build_summary_prompt,
    MAP_PROMPT,
    SUMMARY_PROMPT_TEMPLATE,
    build_system_prompt
)
from app.services.streaming import ndjson, text_from_chunk

logger = logging.getLogger("bpe.summarize")


def split_text_for_map(text: str, chunk_size: int) -> List[str]:
    """Split long text into paragraph blocks approximately chunk_size long."""
    paragraphs = text.split("\n\n")
    blocks = []
    current_block = []
    current_len = 0

    for para in paragraphs:
        p_len = len(para)
        if current_len + p_len > chunk_size and current_block:
            blocks.append("\n\n".join(current_block))
            current_block = [para]
            current_len = p_len
        else:
            current_block.append(para)
            current_len += p_len + 2

    if current_block:
        blocks.append("\n\n".join(current_block))

    return blocks


async def summarize_chunk_task(chunk_text: str, sem: asyncio.Semaphore) -> str:
    """Summarize a single text block with MAP_PROMPT using concurrency limit."""
    async with sem:
        try:
            llm = get_llm(temperature=0.2, streaming=False)
            messages = [
                SystemMessage(content=MAP_PROMPT),
                HumanMessage(content=chunk_text)
            ]
            response = await llm.ainvoke(messages)
            return text_from_chunk(response).strip()
        except Exception as e:
            logger.warning(f"Error in map summarize chunk: {e}")
            return ""


async def stream_summary_response(
    page_id: str,
    style: str,
    request: Request
) -> AsyncGenerator[bytes, None]:
    """Stream summary response for a page using stuff or map-reduce."""
    store = get_page_store()
    page_index = store.get(page_id)
    if not page_index:
        raise err_page_not_found()

    # Emit empty sources event for protocol consistency
    yield ndjson({"type": "sources", "sources": []})

    settings = get_settings()

    try:
        llm = get_llm(temperature=0.3, streaming=True)

        if page_index.char_count <= settings.STUFF_LIMIT_CHARS:
            # Stuff path: single call
            prompt = build_summary_prompt(
                title=page_index.title,
                text=page_index.text,
                style=style
            )
            messages = [HumanMessage(content=prompt)]
        else:
            # Map-reduce path: split, summarize blocks concurrently, then reduce
            blocks = split_text_for_map(page_index.text, settings.MAP_CHUNK_CHARS)
            sem = asyncio.Semaphore(settings.MAP_CONCURRENCY)

            tasks = [summarize_chunk_task(b, sem) for b in blocks]
            mini_summaries = await asyncio.gather(*tasks)
            combined_minis = "\n\n".join([s for s in mini_summaries if s])

            reduce_base = build_system_prompt(style)
            reduce_prompt = SUMMARY_PROMPT_TEMPLATE.format(
                system_base=reduce_base,
                title=page_index.title,
                text=f"Summary of sections:\n{combined_minis}"
            )
            messages = [HumanMessage(content=reduce_prompt)]

        # Stream tokens to client
        async for chunk in llm.astream(messages):
            if await request.is_disconnected():
                logger.info("Client disconnected during summary stream")
                return

            token = text_from_chunk(chunk)
            if token:
                yield ndjson({"type": "token", "text": token})

        yield ndjson({"type": "done"})

    except Exception as exc:
        logger.error(f"Error streaming summary: {exc}")
        app_err = map_llm_exception(exc)
        yield ndjson({
            "type": "error",
            "code": app_err.code,
            "message_bn": app_err.message_bn
        })
