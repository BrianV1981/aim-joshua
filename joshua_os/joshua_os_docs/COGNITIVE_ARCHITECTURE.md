# J.O.S.H.U.A. Cognitive Architecture (The Brain Map)

This document defines the anatomical structure of the J.O.S.H.U.A. memory and continuity layers and how data flows across sessions.

## 1. The Engineering Handoff (`/aim-handoff` & `HANDOFF.md`)
* **Trigger:** Invoked by the active agent at session closeout via the `aim-handoff` skill.
* **Storage:** `HANDOFF.md` at the project root (`0–9` numbered gold-standard template).
* **Mechanism:** Performs an **Idempotent Auto-Wiki Delta Check** first (inspecting `memory-wiki/log.md` and updating `memory-wiki/` if unlogged session work occurred), surgically updates `HANDOFF.md`, seals the session into the Blackbox Vault (`./aim <vessel>-blackbox --session-id <id>`), and atomically pushes both `memory-wiki/` and `HANDOFF.md` directly to `origin/main` (`git add memory-wiki/ HANDOFF.md` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero prompts.

## 2. The Persistent LLM Wiki (`/aim-memory-wiki` & `memory-wiki/`)
* **Trigger:** Invoked mid-session via the `aim-memory-wiki` skill as a fast (~15s) "Save Game" checkpoint, or automatically during Step 1 of `aim-handoff`.
* **Storage:** `memory-wiki/` at the project root (`index.md`, `log.md`, and `pages/*.md` in plain Markdown).
* **Mechanism:** The active agent synthesizes architectural decisions and milestones directly into `memory-wiki/`, runs `./aim index` (or `.\aim.ps1 index` on Windows) so `joshua_os/memory_lance` stays synchronized, and pushes directly to `origin/main` with zero GitHub Issues and zero worktrees.

## 3. Two-Tier Hybrid RAG Engine (LanceDB RAM + Parquet ROM)
* **Trigger:** Native ingestion via `./aim index` (`joshua_os/.aim_core/bootstrap_brain.py`) and local cartridge mounting via `./aim jack-in` (`plugins/datajack/aim_exchange.py`).
* **Storage:**
  * **RAM (`joshua_os/memory_lance`):** Live, mutable LanceDB table indexing `AGENTS.md`, `joshua_os_docs/`, and `memory-wiki/` with SHA-256 cached 768-dim vectors and Tantivy BM25 FTS.
  * **ROM (`joshua_os/archive/cartridges/*.parquet`):** Portable Apache Arrow Parquet cartridges queried via zero-copy reads alongside `memory_lance`.
* **Function:** Hybrid RAG (Vectors + Tantivy FTS + `EntityIntersectionReranker` Reciprocal Rank Fusion), exposed via the `search_lancedb` MCP server (`mcp_lancedb.py`) and `./aim search` CLI fallback.

## 4. Encrypted Blackbox Vault & FTS5 Session Notebook
* **Trigger:** `./aim <vessel>-blackbox --session-id <id>` (or `./aim handoff` / `handoff_pulse_generator.py`).
* **Storage:**
  * **At-Rest Encrypted Archive:** `<project_root>/archive/.raw_jsonl_blackbox/<session_id>.enc` + `manifest.jsonl` (Fernet `AES-128-CBC + HMAC-SHA256`).
  * **Searchable Local Notebook:** `joshua_os/archive/history/<date>_<session_id>.md` and SQLite WAL/FTS5 `joshua_os/archive/history.db`, queried via `./aim sessions`, `./aim search-sessions`, and `./aim recall`.
