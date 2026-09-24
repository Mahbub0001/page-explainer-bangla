# Design Specification: On-Demand Hybrid Lazy Embedding

- **Date:** 2026-09-24
- **Feature:** On-Demand Hybrid Lazy Embedding for Bangla Page Explainer
- **Status:** Approved

## 1. Goal
Drastically improve page indexing speed (from ~6s to <0.1s) and reduce Google Gemini Free-Tier embedding quota usage by ~80% through on-demand lazy embedding and lightweight candidate pre-filtering.

## 2. Architecture & Data Flow

### 2.1 Instant Indexing (`POST /api/v1/pages/index`)
1. Client sends page text.
2. Server splits text into `Document` chunks using `RecursiveCharacterTextSplitter` with Bangla danda delimiter.
3. Chunks are stored directly in `PageIndex.raw_chunks` in memory.
4. An `InMemoryVectorStore` is initialized with `PageIndex.embedded_chunk_ids = set()`.
5. Zero remote API calls are made during indexing.
6. Server returns `PageIndexResponse` in `< 50ms`. The UI immediately transitions to "Ready!".

### 2.2 Direct Summary (`POST /api/v1/summarize`)
1. Summarization reads from `PageIndex.text` (or `raw_chunks`).
2. Calls Gemini Chat LLM with `SUMMARY_PROMPT` directly.
3. Consumes 0 embedding calls.

### 2.3 On-Demand Hybrid Retrieval (`POST /api/v1/chat` and `/api/v1/explain-selection`)
1. **Keyword / BM25 Candidate Selection**:
   - Tokenizes the query into terms (supports Bangla script and English words).
   - Computes BM25/term-frequency scores across `raw_chunks`.
   - Selects top 10-12 candidate chunks, always including the lead chunk (`chunk_id == 0`).
2. **Lazy Embedding of Candidates**:
   - Filters candidate chunks to find those not yet in `embedded_chunk_ids`.
   - If there are unembedded candidates, sends only those (typically 8-12 chunks) to `GoogleGenerativeAIEmbeddings`.
   - Adds them to `vector_store` and records their IDs in `embedded_chunk_ids`.
3. **Semantic Similarity Reranking**:
   - Searches `vector_store` with the query to find the top $K$ ($K=5$) most semantically relevant chunks.
   - Formats context `[1]..[n]` and sources payload.
4. **Streaming Generation**:
   - Streams grounded answer via NDJSON as before.

## 3. Data Model Updates (`services/page_store.py`)
```python
@dataclass
class PageIndex:
    page_id: str
    url: str
    title: str
    text: str
    char_count: int
    chunk_count: int
    truncated: bool
    raw_chunks: List[Document]
    vector_store: InMemoryVectorStore
    embedded_chunk_ids: set[int]
    created_at: float
    last_used: float
```

## 4. Quota Safety & Performance Targets
- Indexing latency: $\le 100\text{ ms}$ (previously 4-6s).
- Indexing quota used: $0$ requests.
- Chat/Explain quota used: $1$ query embed + $\le 12$ chunk embeds $= \le 13$ requests per question (well within 100 RPM).
- Repeated/follow-up questions reuse cached candidate vectors.
