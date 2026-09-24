# Decisions Log

This document records architectural, technical, and design decisions made during the development of Bangla Page Explainer.

## Format
- **Date**: YYYY-MM-DD
- **Decision**: Summary of decision made
- **Reason**: Rationale and context

---

- **Date**: 2026-09-24
  **Decision**: Used the workspace root `chrome_Bangla_page_exp_RAG` directly as the repository root containing `docs/`, `backend/`, and `extension/`.
  **Reason**: The workspace was opened at this folder. Placing files directly in root avoids unnecessary nested directories while matching the exact structure from TRD §3.

- **Date**: 2026-09-24
  **Decision**: Added `numpy` to `backend/requirements.txt`.
  **Reason**: `InMemoryVectorStore` and test fake embeddings require `numpy` for vector calculations and `cosine_similarity`.
