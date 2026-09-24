import json
from typing import Any, AsyncGenerator
from fastapi import Request
from fastapi.responses import StreamingResponse


def ndjson(obj: Any) -> bytes:
    """Serialize dictionary to UTF-8 NDJSON line without ASCII escaping."""
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")


def text_from_chunk(chunk: Any) -> str:
    """
    Extract text from LangChain message chunk.
    Handles str content or list of content blocks (Gemini format).
    Ignores non-text or thinking blocks.
    """
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                # Ignore thinking or metadata blocks
                if block.get("type") == "text" or "text" in block:
                    parts.append(block.get("text", ""))
        return "".join(parts)

    return str(content) if content is not None else ""


def create_streaming_response(generator: AsyncGenerator[bytes, None]) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
