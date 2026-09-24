import time
import hashlib
import asyncio
from typing import Optional, Dict, List, Set
from collections import OrderedDict
from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from app.config import get_settings


@dataclass
class PageIndex:
    page_id: str
    url: str
    title: str
    text: str
    char_count: int
    chunk_count: int
    truncated: bool
    vector_store: InMemoryVectorStore
    created_at: float
    last_used: float
    raw_chunks: List[Document] = field(default_factory=list)
    embedded_chunk_ids: Set[int] = field(default_factory=set)



def normalize_url(url: str) -> str:
    """Normalize URL by stripping fragment and whitespace."""
    return url.split("#")[0].strip()


def compute_page_id(url: str, text: str) -> str:
    """Generate 16-character SHA-256 hex digest of normalized url + text."""
    normalized = normalize_url(url)
    content = f"{normalized}\n{text}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()[:16]


class PageStore:
    def __init__(self):
        self._cache: OrderedDict[str, PageIndex] = OrderedDict()
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def purge_expired(self):
        """Remove entries that have exceeded CACHE_TTL_SECONDS."""
        settings = get_settings()
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if (now - v.last_used) > settings.CACHE_TTL_SECONDS
        ]
        for k in expired_keys:
            self._cache.pop(k, None)
            self._locks.pop(k, None)

    def get(self, page_id: str) -> Optional[PageIndex]:
        """Retrieve a cached page index, updating last_used and LRU position."""
        self.purge_expired()
        if page_id in self._cache:
            entry = self._cache[page_id]
            entry.last_used = time.time()
            self._cache.move_to_end(page_id)
            return entry
        return None

    def put(self, index: PageIndex):
        """Store a page index in LRU cache, evicting oldest if capacity reached."""
        self.purge_expired()
        settings = get_settings()

        if index.page_id in self._cache:
            self._cache.move_to_end(index.page_id)
        else:
            if len(self._cache) >= settings.CACHE_MAX_PAGES:
                # Evict oldest entry (LRU)
                oldest_key, _ = self._cache.popitem(last=False)
                self._locks.pop(oldest_key, None)

        self._cache[index.page_id] = index

    def get_lock(self, page_id: str) -> asyncio.Lock:
        """Get or create an asyncio.Lock for a specific page_id."""
        if page_id not in self._locks:
            self._locks[page_id] = asyncio.Lock()
        return self._locks[page_id]

    def count(self) -> int:
        self.purge_expired()
        return len(self._cache)

    def clear(self):
        self._cache.clear()
        self._locks.clear()


_page_store = PageStore()


def get_page_store() -> PageStore:
    return _page_store
