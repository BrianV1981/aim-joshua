# J.O.S.H.U.A. Protocol: LanceDB Ingestion, Locking & Compaction

## Overview
This protocol defines how `joshua_os/.aim_core/bootstrap_brain.py` and `joshua_os/.aim_core/lance_backend.py` chunk, embed, update, lock, and compact project documentation inside `joshua_os/memory_lance`.

## 1. Length-Constrained Accumulator Chunking
`joshua_os/.aim_core/plugins/datajack/forensic_utils.py` (`chunk_text`) splits Markdown and source documents along paragraph boundaries (`\n\n`) rather than arbitrary fixed-token windows:
- Paragraph blocks are accumulated until reaching **500–1,500 characters** before flushing a chunk.
- Oversized single blocks (>1,500 characters) are split cleanly so every chunk stays focused for both semantic embedding and Tantivy BM25 ranking.

## 2. Incremental SHA-256 Vector Caching & Offline Resilience
When `./aim index` (`bootstrap_brain.py`) runs:
1. Each discovered file (`AGENTS.md`, `joshua_os/joshua_os_docs/**/*.md`, `memory-wiki/**/*.md`) is keyed by its deterministic repo-relative `session_id` (`foundation-<relpath>` or `wiki-<relpath>`).
2. Before recomputing embeddings, `bootstrap_brain.py` loads existing `(session_id, content_sha256) -> vector` mappings from `memory_lance`.
3. **Online Ollama (`http://127.0.0.1:11434`):** Unchanged chunks reuse their cached 768-dim float32 vectors immediately; only new or edited chunks call Ollama (`nomic-embed-text`).
4. **Offline / CI Fallback:** When Ollama is unreachable (`use_embeddings=False`), previously embedded non-zero 768-dim vectors are **preserved intact** for unchanged chunks, and new chunks fall back to Tantivy BM25 FTS (`[0.0] * 768`) until Ollama is next online.

## 3. Concurrency Safety & Version Compaction
Because the `search_lancedb` MCP server (`mcp_lancedb.py`) may read `memory_lance` concurrently while `./aim index` or `./aim clean` writes to it:
- **Cross-Platform Write Lock:** All `VectorBackend` mutating operations (`upsert_fragments`, `add_fragments`, `delete_by_session_ids`, `rebuild_fts_index`, `compact`) acquire an exclusive file lock (`memory_lance/.aim_write.lock`) via `fcntl.flock` on POSIX or `msvcrt.locking` on Windows.
- **SQL Literal Escaping:** All LanceDB DataFusion `.where(...)` and `.delete(...)` predicates escape string literals via `sql_quote()` (doubling `'`) and cast integer IDs explicitly.
- **Reader-Safe Compaction Window:** Live `upsert_fragments()` and `./aim clean` (`joshua_os/.aim_core/maintenance.py`) run `table.optimize(cleanup_older_than=timedelta(minutes=5))` so active concurrent readers never hit `FileNotFoundError` on recently superseded `.lance` data files. Immediate zero-retention compaction (`cleanup_older_than=timedelta(seconds=0)`) is reserved exclusively for offline seed baking (`bootstrap_brain.py --seed-default-lance` or `maintenance.py --immediate`).
