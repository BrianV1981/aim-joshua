# J.O.S.H.U.A. Core Engine (`joshua_os/.aim_core/`)

This directory contains the Python runtime modules that power the J.O.S.H.U.A. exoskeleton across Linux, macOS, WSL, and Windows 10/11. Operators and agents typically invoke these modules through `./aim` (POSIX) or `.\aim.ps1` / `aim.cmd` (Windows).

## Key Components
* **`aim_cli.py`, `cli_memory.py`, `cli_vault.py`**: The central CLI router, memory/cartridge maintenance commands, and encrypted Blackbox Vault handlers.
* **`mcp_lancedb.py`, `retriever.py`, `lance_backend.py`**: The FastMCP `search_lancedb` server and Two-Tier Hybrid RAG engine (LanceDB vectors + Tantivy BM25 FTS + RRF reranking + zero-copy Parquet cartridge search).
* **`bootstrap_install.py` & `bootstrap_brain.py`**: Pure-Python cross-platform project installer (`clean`, `agent`, `core` modes) and incremental SHA-256 cached LanceDB indexer.
* **`blackbox_vault.py` & `extract_signal.py`**: Fernet (`AES-128-CBC + HMAC-SHA256`) at-rest session archival, manifest verification, noise-reduced Flight Record extraction, and SQLite WAL/FTS5 `history.db` indexing.
* **`config_utils.py`, `register_mcp.py`, `agy_workspace_trust.py`**: Portable `CONFIG.json` resolution, non-destructive multi-harness MCP registration, and Antigravity workspace trust management.
