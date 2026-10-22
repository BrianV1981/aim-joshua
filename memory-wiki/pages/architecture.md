# Architecture

## The OS Framework
J.O.S.H.U.A. is a CLI-agnostic operating system designed to serve as the foundational brain for autonomous AI agents. The framework has entirely decoupled from legacy "CLI vessels" (e.g., aim-grok, aim-opencode). 

## Memory Synthesis & Direct-to-`main` State (#101)
The system utilizes a Just-In-Time (JIT) memory synthesis approach where Agent Memory (`memory-wiki/**` and `HANDOFF.md`) is treated as living OS state exempt from code worktree GitOps:
- The legacy `_ingest/` drop zone and background `session_summarizer.py` daemons have been abolished. 
- **Mid-Session "Save Game" (`/aim-memory-wiki`):** Conscious Agents invoke `aim-memory-wiki` synchronously to synthesize recent architectural changes into `memory-wiki/`, run `./aim index`, and push directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero issues, zero worktrees, and zero prompts.
- **One-Command Closeout (`/aim-handoff`):** At session closeout, `aim-handoff` performs an **Idempotent Auto-Wiki Delta Check** on `memory-wiki/log.md` (automatically updating `memory-wiki/` first if unlogged session work occurred), surgically updates `HANDOFF.md` (`0–9` template), and pushes both `memory-wiki/` and `HANDOFF.md` to `origin/main` in a single atomic commit.
- During system boot or `./aim index`, the root `PROJECT_ROOT/memory-wiki/` and `AIM_ROOT/joshua_os_docs/` are embedded directly into the `memory_lance` LanceDB RAM pool.

### The Ingestion Engine (`bootstrap_brain.py`) & Pre-Baked `default_lance` (#101, #103–#104)
The primary vector ingestion engine has been hardened against configuration drift. It recursively parses (`**/*.md` with file-path deduplication) both the root `PROJECT_ROOT/memory-wiki/` and `AIM_ROOT/joshua_os_docs/` trees to ensure zero blindspots during bootstrapping. Agents can trigger this explicitly by calling `aim index`, or ingest custom external documentation via `aim index --dir <path>`.
- **Pre-Baked `default_lance` Snapshot (`364 KB`, `58` Fragments):** Fresh `curl` installs seed `joshua_os/memory_lance/` from `joshua_os/assets/default_lance/`, which is built in a single atomic transaction containing the canonical `AGENTS.md` and `joshua_os_docs/` so new projects have `v0.8.4` OS rules in their vector DB out-of-the-box.
- **Dynamic `LANCE_DB_PATH` Resolution (`lance_backend.py`):** `VectorBackend.__init__(self, path=None)` resolves `self.path = path or LANCE_DB_PATH` at instantiation time rather than import time, ensuring runtime overrides from `mcp_lancedb.py` take effect immediately.
- **Onboarding `AGENTS.md` Protection (`aim_init.py` & `BOOTSTRAP.md`):** `aim_init.provision_agents_md()` backed by `joshua_os/.aim_core/templates/default_AGENTS.md` guarantees `./aim init` (interactive or `--headless --persona <name>`) never truncates `AGENTS.md` to a stub, and `install-agent.sh [persona]` automatically resolves specialist blueprints from `aim-coagents`.

## The Skill Library Architecture
The `aim-skill-library` utilizes a **Base + Override** architecture. All universal tool skills reside in the global `skills/` directory. However, when a specific vessel requires unique mechanics (e.g., `aim-handoff` triggering distinct `agy-blackbox` or `grok-blackbox` commands), the vessel-specific override is stored in `vessels/<cli>/skills/`. The installation script seamlessly detects and links the override, falling back to the global base if none exists.

## TUI Cockpit (aim_config.py)
The TUI has been strictly scoped down to OS-level environment management. It no longer contains logic for modifying agent personas, modifying markdown files via regex, or toggling legacy background daemons. Its mandate is limited to:
- Secret Vault & API Key Management
- LLM Cognitive Tier Routing (RAG Model Matrix)
- MCP Server Configuration
- Archive Retention settings

## Handoff vs Reincarnation
The original `reincarnation` sub-package (which automatically spawned new terminals via background hooks) has been completely purged from the codebase. It has been 100% superseded by the `aim-handoff` skill, placing the responsibility of context teleportation back into the hands of the conscious agent rather than unpredictable background daemons.

## Tool Injection (MCP)
J.O.S.H.U.A. operates with a strict "Two-Tier Protocol" for extending capabilities (such as the LanceDB memory pool).
- **Primary (Native MCP):** Modern CLI harnesses automatically ingest the local MCP server (`mcp_lancedb.py`), natively granting the active agent the `search_lancedb` internal tool. The MCP server dynamically binds to the active workspace to prevent cross-contamination.
- **Local-First + Umbrella Subfolder Fallback (#94 & #99):** When `workspace_path/joshua_os/memory_lance` exists locally, `mcp_lancedb.py` queries strictly that single project database (zero cross-project bleed). If the CLI is launched in a parent/umbrella directory (e.g., `/home/kingb/aim-agents/`) with no root database, `mcp_lancedb.py` automatically discovers immediate `*/joshua_os/memory_lance` subfolders, queries each read-only, tags hits with `[<subfolder>]`, and returns the top-K results by score without adding parameters to the MCP tool signature. `retriever.py` dynamically resolves `archive/cartridges` and `archive/flashrank_cache` from `lance_backend.LANCE_DB_PATH` (`get_active_aim_root()`) so Sandwich Context Expansion and Datajack cartridges track the active child project.
- **Fallback (CLI-Agnostic):** To ensure 100% interoperability with legacy or custom CLI loops, agents gracefully degrade to direct python subprocess shell commands (e.g., `aim_cli.py search`) if an MCP tool is not present in their prompt. This guarantees no agent is ever completely blind.

## Modular CLI Router (`aim_cli.py`, `cli_vault.py`, `cli_memory.py`) & Cross-Platform Support (#98)
The CLI router (`joshua_os/.aim_core/aim_cli.py`) has been decomposed into focused domain modules while preserving top-level symbol re-exports and native Windows 10/11 + Linux/macOS execution (`aim`, `aim.ps1`, `aim.cmd`, and `resolve_venv_python` in `config_utils.py`):
- **`aim_cli.py`**: Core pure-Python GitOps (`fix`, `push` via `git_push_changes` with `--include-untracked` / `-a`, `promote`, `merge-batch`, `prune-remote`, `bug`, `projects`), RAG dispatch (`search`, `map`, `index`), diagnostics (`doctor`, `health`, `status`), and `update`.
- **`cli_vault.py`**: Forensic blackbox and Handoff vNext handlers (`cmd_vault`, `cmd_agy_blackbox`, `cmd_grok_blackbox`, `cmd_codex_blackbox`, `cmd_opencode_blackbox`, `cmd_handoff_vnext`).
- **`cli_memory.py`**: Cartridge exchange, session recall/audit, and rolling archive maintenance (`cmd_clean`, `cmd_sync`, `cmd_audit`, `cmd_recall`, `cmd_bake`, `cmd_exchange`, `cmd_jack_in`, `cmd_unplug`, `cmd_purge`, `cmd_uninstall`, `cmd_import`).
- Deprecated `swarm` CLI routes were removed from `aim_cli.py` in favor of `aim-coagents` blueprints (`install-agent.sh`) and `aim-communicate` tmux messaging.

