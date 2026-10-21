# A.I.M. Cognitive Architecture (The Brain Map)

This document defines the complete anatomical structure of the A.I.M. "Brain" and how data flows through the system. Future agents must reference this map to understand where state lives and how memory is retrieved.

## 1. The Failsafe Snapshot Layer
*   **Trigger:** Executed silently in the background on every turn by `hooks/failsafe_context_snapshot.py`.
*   **Storage:** `continuity/INTERIM_BACKUP.json` and `continuity/FALLBACK_TAIL.md`.
*   **Purpose:** Ephemeral session rescue. If the agent crashes (e.g., V8 OOM), `aim crash` uses these files to reconstruct the active state without data loss.

## 2. The Engineering Handoff (`/aim-handoff`)
*   **Trigger:** Invoked synchronously by the active agent at session closeout via the `aim-handoff` skill.
*   **Storage:** `HANDOFF.md` at the project root (`0–9` numbered gold-standard template).
*   **Mechanism:** Performs an **Idempotent Auto-Wiki Delta Check** first (inspecting `memory-wiki/log.md` and updating `memory-wiki/` if unlogged session work occurred), surgically updates `HANDOFF.md`, seals the session into the Blackbox Vault (`./aim <vessel>-blackbox --session-id <uuid>`), and atomically pushes both `memory-wiki/` and `HANDOFF.md` directly to `origin/main` (`git add memory-wiki/ HANDOFF.md` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero prompts.
*   **Purpose:** To teleport tactical context and persistent lore to a fresh agent in a single turn without worktree/issue overhead.

## 3. The Persistent LLM Wiki (`/aim-memory-wiki`)
*   **Trigger:** Invoked mid-session via the `aim-memory-wiki` skill as a fast (~15s) "Save Game" checkpoint, or automatically during Step 1 of `aim-handoff`.
*   **Storage:** `memory-wiki/` directory (`index.md`, `log.md`, and `pages/*.md` in native Markdown).
*   **Mechanism:** The active Conscious Agent synthesizes recent architectural decisions and milestones directly into `memory-wiki/`, runs `./aim index` when LanceDB is active, and pushes directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero GitHub Issues, zero worktrees, and zero confirmation prompts. *(The legacy `_ingest/` drop zone and background `session_summarizer.py` daemons have been abolished).*
*   **Purpose:** Human-readable, compounding architectural memory.

## 4. The Native Parquet & LanceDB Engine (The Subconscious)
*   **Trigger:** Native ingestion via `./aim index` (`bootstrap_brain.py`) or via `./aim jack-in` for external cartridges.
*   **Storage:** 
    *   **RAM:** `joshua_os/memory_lance` (The live, mutable pool of foundation docs, `memory-wiki/`, and flight recorders).
    *   **ROM:** `joshua_os/archive/cartridges/*.parquet` (Immutable, highly-compressed skill packages).
*   **Function:** Hybrid RAG (Semantic Vectors + Tantivy FTS + FlashRank reranking), exposed via the `search_lancedb` MCP server (Primary) and `./aim search` CLI (Fallback).
*   **Purpose:** Token-efficient, zero-latency semantic retrieval for the Conscious Agent.

## 5. Eternal Recall (History Search)
*   **Trigger:** The `aim_core/handoff_pulse_generator.py` script.
*   **Storage:** `archive/history/` (Markdown).
*   **Function:** The raw markdown transcript of the dying session is saved here. It acts as the master ledger.

## 6. Sovereign Synchronization (The Export Layer)
*   **Trigger:** `aim_core/sovereign_sync.py` running during `aim push`.
*   **Storage:** `archive/sync/`
*   **Function:** Translates the binary LanceDB memory into deterministic `.jsonl` files.
*   **Purpose:** Git-friendly, mergeable brain backups.
