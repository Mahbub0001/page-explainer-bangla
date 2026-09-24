import re
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_settings


def chunk_text(text: str, page_id: str, title: str) -> Tuple[List[Document], bool]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter with Bangla danda.
    Drops chunks with < 20 non-whitespace chars.
    Caps total chunks to MAX_CHUNKS.
    Returns (list_of_documents, was_truncated).
    """
    settings = get_settings()

    separators = ["\n\n", "\n", "।", ". ", "? ", "! ", "; ", ", ", " ", ""]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=separators,
    )

    raw_chunks = splitter.split_text(text)

    # Filter out tiny chunks (< 20 non-whitespace characters)
    meaningful_chunks = [c for c in raw_chunks if len(re.sub(r"\s+", "", c)) >= 20]

    truncated = False
    if len(meaningful_chunks) > settings.MAX_CHUNKS:
        meaningful_chunks = meaningful_chunks[:settings.MAX_CHUNKS]
        truncated = True

    documents = []
    for i, chunk in enumerate(meaningful_chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "chunk_id": i,
                "page_id": page_id,
                "title": title
            }
        )
        documents.append(doc)

    return documents, truncated
