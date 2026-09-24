# On-Demand Hybrid Lazy Embedding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement on-demand lazy chunk embedding and BM25 candidate selection so page indexing takes <0.1s with 0 API calls, and Q&A only embeds relevant candidate chunks.

**Architecture:** Indexing stores `raw_chunks` in memory and returns immediately. When `retrieve_context` is invoked in chat or explain-selection, a lightweight BM25 scorer ranks candidates, only the top 12 candidate chunks are embedded and cached in `InMemoryVectorStore`, and semantic similarity retrieval returns the top-5 grounded chunks.

**Tech Stack:** FastAPI, LangChain Core, Google Generative AI Embeddings, Python asyncio.

## Global Constraints
- Must maintain 100% compatibility with Chrome extension API contracts (`POST /api/v1/pages/index`, `/chat`, `/summarize`, `/explain-selection`).
- All existing tests in `backend/tests/` must remain passing.
- Response streaming order (`sources` -> `token`... -> `done`) must be preserved.

---

### Task 1: Update `PageIndex` in `page_store.py`
**Files:**
- Modify: `backend/app/services/page_store.py`

- [x] Add `raw_chunks: List[Document]` and `embedded_chunk_ids: set[int]` to `PageIndex` dataclass.

### Task 2: Update `pages.py` for Instant Zero-API Indexing
**Files:**
- Modify: `backend/app/routers/pages.py`

- [x] In `index_page`, chunk the text, initialize `InMemoryVectorStore`, create `PageIndex` with `raw_chunks=chunks` and `embedded_chunk_ids=set()`, and return response immediately without calling `aadd_documents` upfront.

### Task 3: Implement BM25 Pre-filtering and Lazy Embedding in `rag.py`
**Files:**
- Modify: `backend/app/services/rag.py`

- [x] Implement `select_candidate_chunks(raw_chunks, query, top_n=12)` using term-matching and lead-chunk inclusion.
- [x] In `retrieve_context(page_index, query, k=5)`, find unembedded candidates, embed only them with `embeddings.aembed_documents`, store in `vector_store`, and execute semantic search.

### Task 4: Run Tests and Verify All Pass
**Files:**
- Modify: `backend/tests/test_pages.py` (if any mock updates needed)
- Modify: `backend/tests/test_chat.py`
- Test: `pytest -q`

- [x] Run pytest to verify all existing and new unit tests pass.

### Task 5: Live Verification & Commit
**Files:**
- Test with live backend on Wikipedia Solar System
- Commit git changes
- [x] Verified with live end-to-end script on 62k char Bangla article and Gemini API.

