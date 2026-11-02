# The Codebase Map (`joshua_os/` — v1.1.3)

This document maps every active Python module and hook in `joshua_os/`. Use it to locate exact implementation boundaries before modifying engine behavior.

---

## 1. Core Storage, Retrieval & Configuration (`joshua_os/.aim_core/`)
* **`config_utils.py`**: Portable `CONFIG.json` loader (`joshua_os/.aim_core/CONFIG.json`), atomic relocation-only config persistence, Antigravity 2.0 + legacy path resolution, and cross-platform venv Python discovery.
* **`lance_backend.py`**: PyArrow/LanceDB table wrapper (`memory_lance`), cross-platform file write lock (`fcntl`/`msvcrt`), SQL literal quoting, `EntityIntersectionReranker` (Reciprocal Rank Fusion), and safe version compaction.
* **`retriever.py`**: Two-Tier Hybrid RAG search engine combining LanceDB (`memory_lance` + optional umbrella fallback) with zero-copy mounted `.parquet` cartridges and N-1/N+1 sandwich context expansion.
* **`mcp_lancedb.py`**: FastMCP server exposing `search_lancedb` over stdio with dynamic workspace root resolution and zero global path mutation.
* **`bootstrap_brain.py`**: Incremental foundation/wiki indexer (`AGENTS.md`, `joshua_os_docs/`, `memory-wiki/`) with SHA-256 chunk vector caching so offline runs preserve existing 768-dim embeddings.
* **`reasoning_utils.py`**: Multi-provider LLM client (Antigravity headless, Anthropic, OpenAI/OpenRouter, Ollama, Codex) configured via `CONFIG.json` and OS keyring.

---

## 2. CLI Routers, Installers & Onboarding (`joshua_os/.aim_core/`)
* **`aim_cli.py`**: Primary CLI entry point (`COMMAND_HANDLERS`), GitOps worktree commands (`bug`, `bug-operator`, `fix`, `promote`, `push`, `prune-remote`, `merge-batch`), and release-pinned Zip-Slip-guarded `cmd_update`.
* **`cli_memory.py`**: Memory, cartridge, and lifecycle handlers (`sessions`, `search-sessions`, `bake`, `exchange`, `jack-in`, `unplug`, `clean`, `audit`, `recall`, `OS_DIR`-scoped `purge`, and host-safe `uninstall`).
* **`cli_vault.py`**: CLI handlers for `vault`, `handoff-vnext`, `agy-blackbox`, `grok-blackbox`, `codex-blackbox`, and `WHERE session_id = ?`-scoped `opencode-blackbox`.
* **`bootstrap_install.py`**: Pure-Python cross-platform installer (`--mode clean|agent|core`) invoked by `install*.sh` and `install*.ps1`.
* **`aim_init.py`**: Workspace initializer, `AGENTS.md` template/persona provisioner, non-destructive Antigravity hook registrar, and POSIX `tmux` onboarding launcher.
* **`register_mcp.py` & `agy_workspace_trust.py`**: Non-destructive `search_lancedb` MCP auto-registration (preserving JSONC/malformed user files) and Antigravity trusted-workspace registration.
* **`aim_projects.py`**: GitHub Projects v2 GraphQL/`gh project` Kanban integration (`board`, `in-progress`, `done`, `blocked`, `doctor`).
* **`aim_config.py`, `aim_doctor.py`, `aim_batch_merge.py`, `aim_delegate.py`, `aim_router.py`**: Interactive configuration menu, dependency validator, batch branch merger, parallel file analyzer, and hook path router.

---

## 3. Session Continuity, Vault & Maintenance (`joshua_os/.aim_core/` & `joshua_os/handoff/`)
* **`blackbox_vault.py`**: Fernet (`AES-128-CBC + HMAC-SHA256`) at-rest session sealer (`archive/.raw_jsonl_blackbox/`), shrink-overwrite guard (`--force`), SHA-256 manifest verifier, and SQLite WAL `history.db` indexer.
* **`aim_vault.py`**: OS keyring secret helper and `aim vault doctor` diagnostics.
* **`extract_signal.py` & `session_naming.py`**: Pure-Python transcript noise stripper and human-readable Flight Record renderer.
* **`handoff_pulse_generator.py`, `heartbeat.py`, `maintenance.py`, `audit_tools.py`, `recall_tools.py`**: Continuity pulse generator, `aim health` check, rolling archive janitor + locked LanceDB compaction, and session synthesis helpers.
* **`joshua_os/handoff/` (`cli.py`, `handoff_core.py`, `blackbox_cron.py`, `flight_record.py`, `embed_store.py`, `packet.py`, `paths.py`, `adapters/`)**: Structured Handoff vNext pipeline (`handoff`, `blackbox-cron`, `e2e-staged`).

---

## 4. DataJack Plugins & Hooks
* **`joshua_os/.aim_core/plugins/datajack/` (`aim_bake.py`, `aim_exchange.py`, `forensic_utils.py`)**: Length-Constrained Accumulator text chunker, `.parquet` ROM compiler, and local cartridge mount/unplug manager.
* **`joshua_os/hooks/cognitive_mantra.py`**: Active `AfterTool` anti-drift reminder hook invoked through `aim_router.py`.
