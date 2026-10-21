# Memory Log

## [2026-08-11] ingest | Initial Bootstrap & Legacy Purge
- Bootstrapped the memory wiki structure.
- Ingested architectural changes regarding the removal of legacy CLI vessels and the transition to the JIT `aim-memory-wiki` workflow.
- Documented GitOps worktree execution models and new clean installation pathways.

## [2026-08-11] ingest | GitHub Projects CLI Integration
- Ingested Issue #21 context regarding the new `aim projects` Kanban CLI wrapper.
- Created `pages/projects.md` detailing the agent board protocol and required OAuth scopes.

## [2026-08-11] ingest | Handoffs, GitOps, and Retrieval Protocols
- Documented the transition from "Reincarnation" to "Handoff", including the mandatory vessel-specific Blackbox vault session sealing (`aim agy-blackbox`).
- Enforced the GitOps worktree workflow inside the `aim-memory-wiki` skill.
- Documented the Base + Override architecture of the `aim-skill-library`.
- Documented the explicit `python3 joshua_os/.aim_core/aim_cli.py search` command requirement for RAG retrieval to avoid bash alias confusion.
- Created `pages/handoff-and-retrieval.md` and updated `pages/architecture.md` and `pages/active-memory-protocol.md`.

## [2026-08-12] ingest | Docs Synchronization & Operator Guide
- Synced `joshua_os_docs/` to perfectly reflect the `memory-wiki/` ground truth (Issue #26). Abolished the legacy `REINCARNATE_PROTOCOL.md` and replaced it with `HANDOFF_PROTOCOL.md`.
- Formally injected `aim projects` and `aim agy-blackbox` into the `AIM_CLI_TOOLS.md` cartidge documentation.
- Extracted the human-facing "Operator Guide" away from the OS protocols into the external GitHub Wiki.
- Appended a strict `aim-memory-wiki` prerequisite to the `aim-handoff` skill in the `aim-skill-library`.

## [2026-08-12] ingest | Blackbox Vault Forensic Protocol
- Created `BLACKBOX_VAULT.md` in `joshua_os_docs/` to formally document the Vault as an Operator-locked, anti-tampering forensic archive (Issue #28).
- Synced the documentation into `memory-wiki/pages/blackbox-vault.md` to establish the intent that agents cannot edit their own history to cover up mistakes.

## [2026-08-12] ingest | Audit #3 Polish Sprint Resolution
- Resolved issues #49-54 for the Audit #3 Polish Sprint.
- `aim search` upgraded to provide human-readable text by default, with `--json` for machine dumps.
- CI pipeline deepened to test `aim doctor`, `aim map`, and `aim search`.
- `aim vault doctor` implemented for diagnosing Blackbox file-key backups.
- CLI Parser strictness increased: removed silent search fallbacks and purged legacy `--context` parameters.
- `CONTRIBUTING.md` formalized to mandate the 3-step GitOps workflow (`aim bug` -> `aim fix` -> `aim promote`).
- Discovered and logged bug (#57) for `aim_batch_merge.py` hardcoding `main` instead of using dynamic branch resolution.

## [2026-08-12] ingest | Final Audit #3 Polish & Testing CI/CD
- Fixed the hardcoded branch parsing in `aim_batch_merge.py` via dynamic `git branch --list` checks (Issue #57).
- Wired the `aim vault doctor` explicitly under the `aim vault` parser (Issue #59).
- Abstracted the `SOURCE.md` Runtime to strictly `CLI-agnostic` (Issue #60).
- Purged stale `wiki_tools` imports causing ModuleNotFound errors in core files (Issue #61).
- Discovered and documented architectural bug: `aim_push.sh` strictly relies on `git add -u`, explicitly ignoring newly created untracked files unless manually staged prior.
- Built a localized robust `pytest` harness containing E2E simulated git repository mocking to validate `aim promote` dynamically without disrupting the Operator's host system (Issues #63-64).
- Hardened CI environment using the `gitleaks` GitHub action for rigid secrets scanning (Issue #65).
- Created a new wiki page `pages/ci-testing.md` to catalog the test scaffolding.

## [2026-08-12] ingest | Audit 6 to 8: A+ Sprint, Offline CI, and Orchestrator Freeze
- Ingested Audit Pass 6, Pass 7, and Pass 8 (A+ Sprint) findings.
- Documented architectural CI blindspots: Infrastructure variations (like the Semantic Engine being offline in GHA) can break parsers if text warnings (`[NOTICE]`) precede JSON array outputs on standard output.
- Documented the strict A+ Acceptance Bar: no process theater ("A+ / incredibly robust" claims), 100% path coverage via testing (hermetic vault decrypts, exact CLI behavior), and zero closures on red CI.
- Documented the `FREEZE` Orchestrator Override protocol: If the orchestrator (`grok-audit`) takes over the tree to fix CI, the active agent must immediately stay idle and NOT push, promote, or edit.
- Added `pages/audit-protocol.md` to detail the A+ and override mechanics.
- Updated `pages/ci-testing.md` with offline/hermetic test warnings.

## [2026-08-26] ingest | TUI Cockpit Overhaul & Reincarnation Purge
- Formally deleted the `reincarnation/` sub-package and `aim_reincarnate.py` script. The "Reincarnation" mechanic is entirely obsolete, fully replaced by the `aim-handoff` skill.
- Overhauled the Interactive TUI Cockpit (`aim_config.py`), stripping all abandoned legacy hooks (e.g. Subconscious Daemon, Cognitive Mantras).
- Removed brittle markdown regex parsers from the TUI. The TUI is now strictly scoped to managing API Keys, LLM Cognitive Tiers, the Secret Vault, and the MCP Server.
- Synced `joshua_os_docs/` to reflect these changes. Updated `pages/architecture.md`.

## [2026-08-26] ingest | LanceDB MCP Server Migration
- Migrated LanceDB semantic search from a shell execution (`aim_cli.py search`) to a native Python MCP Server (`mcp_lancedb.py`).
- Updated the system to register `search_lancedb` as an internal agent tool.
- Implemented a dynamic workspace handshake: the MCP server reads `params.workspaceFolders[0].uri` from the client's initialize payload to dynamically locate `memory_lance/`.
- Updated `install.sh` and `install-agent.sh` to automatically write the server definition to the Operator's global `~/.gemini/config/mcp_config.json`.
- Updated `HYBRID_SEARCH.md` and `handoff-and-retrieval.md` to reflect the new tool-calling architecture over legacy shell commands.
- **Addendum**: Established the "Two-Tier Protocol" for retrieval in AGENTS.md, defining MCP as the primary pathway and `aim_cli.py search` as the strict fallback to maintain J.O.S.H.U.A.'s CLI-agnostic mandate.

## [2026-08-27] ingest | Architecture Sync for Two-Tier Protocol
- Ingested the Two-Tier Protocol (MCP + Fallback) architectural strategy into `pages/architecture.md`.
- Verified that the "CLI-Agnostic" foundational mandate is firmly defended in the wiki's core logic.

## [2026-08-28] ingest | Configuration Drift, Testing, and Ingestion Blindspot Fixes
- Implemented automated `pytest` coverage for the new MCP Server (`mcp_lancedb.py`) and the ingestion engine (`bootstrap_brain.py`) to fulfill TDD mandates.
- Fixed a major ingestion blindspot in `bootstrap_brain.py`: updated `glob.glob` to use `recursive=True` ensuring subdirectories within `memory-wiki/` and `joshua_os_docs/` are correctly indexed.
- Parameterized `bootstrap_brain.py` with an `argparse` `--dir` flag.
- Discovered and resolved a CLI router bug in `aim_cli.py` where the `aim index` command dropped its arguments. The CLI now correctly forwards the `--dir` flag to the ingestion engine.
- Documented the `aim index [--dir <path>]` command in `joshua_os_docs/AIM_CLI_TOOLS.md`.

## [2026-08-28] ingest | DHH Agentic Philosophy & OS Alignment
- Ingested the findings from the Lex Fridman Podcast #501 (David Heinemeier Hansson on Agentic Engineering).
- Documented the architectural shift towards "Outcome-Oriented Directives" (the agent defines the "how", the Operator provides the "what").
- Logged the "Elevated Operator Role" (agents handle syntax/mechanics; humans handle taste/design).
- Documented the "Plain-Text & CLI Ascendancy" mandate (Unix Philosophy) emphasizing flat files and CLI over GUIs.
- Logged the "Agentic Gatekeeper" pre-flight review protocol.
- Created `pages/dhh-agentic-philosophy.md` to formally catalog these new core OS directives and updated `index.md` to link to it.

## [2026-09-22] ingest | Integration of Direct Execution Protocol (i-have-adhd)
- Evaluated the `i-have-adhd` skill repository and identified its core conversational efficiency rules (No Preambles, Numbered Steps, Lead with Action).
- Wove these rules directly into the core `AGENTS.md` and active ecosystem blueprints (`aim-connect`, `aim-tmux-dashboard`, `aim-coagents`) rather than keeping them as an opt-in skill.
- Clarified the architectural distinction between *opt-in skills* and *innate DNA* (`AGENTS.md`).
- Updated `pages/dhh-agentic-philosophy.md` to document this new conversational mandate.

## [2026-10-19] ingest | CLI Modularization, Co-Agent Engine Update Hardening, and A+ Test Expansion (#87–#93)
- Reconciled local Git/worktree drift (#87) and purged 95 stale remote and 72 local `archive-fix/*` / `fix/issue-*` branches (#88).
- Removed deprecated `swarm` CLI routes (`cmd_swarm` and `swarm` subparser) from `aim_cli.py` (#89) and standardized `README.md` to the `<!-- AIM_ECOSYSTEM_START -->` protocol (#90).
- Hardened `cmd_update` (#92) to support `--source <path>` and `--skip-deps`, guard optional engine subdirectories (`scripts/`), and strictly preserve `.aim_core/CONFIG.json` alongside Co-Agent blueprint/wiki/artifact files.
- Modularized `aim_cli.py` (#93) by extracting vault/blackbox handlers into `cli_vault.py` and memory/cartridge/maintenance handlers into `cli_memory.py`, fixed broken `.aim_core` relative imports in `audit_tools.py`, `recall_tools.py`, and `cmd_sync`, implemented `cmd_clean`, added worktree venv fallback to `./aim`, and expanded `pytest` coverage to 25 tests.
- Verified Pass 9 Delta Audit by `aim-auditor` (#91) upgrading `AUDIT_AIM_JOSHUA.md` to **Overall Grade: A+**.
- Implemented Pure Automatic Mode (Local-First + Subfolder Fallback) in `mcp_lancedb.py` (#94) and guarded `aim_cli.py` top-level `os.execv` behind `if __name__ == "__main__":`, expanding `pytest` coverage to 27 passing tests.
- Hardened `joshua_os/install.sh` and `joshua_os/install-agent.sh` (#95) with `$HOME`/`/` safety guards, aligned `install.sh` to copy only `joshua_os/`, `AGENTS.md` (`cp -n`), and `TOOLS.md` (`cp -n`) with `git init` and AGY workspace trust registration, fixed `aim_projects.py` `item-add` JSON parsing for >200-item boards, and overhauled `README.md` with explicit `mkdir/cd`, `doctor`, and project customization onboarding instructions (`28/28` pytest passing).

## [2026-10-20] ingest | Consumer `.gitignore` Safeguard, Atomic `./aim` Replacement, and 16-Repo Fleet Rollout (`v0.7.3`)
- Added automatic `.gitignore` exoskeleton population (`joshua_os/`, `aim`, `workspace/`, `archive/`) to `joshua_os/install.sh`, `joshua_os/install-agent.sh`, and `cmd_update` (`ensure_consumer_gitignore` in `aim_cli.py`, skipping upstream `aim-joshua` via `is_upstream_engine_repo`) (#96, `29/29` pytest passing).
- Discovered and fixed an in-place bash script overwrite bug in `cmd_update`: replacing `./aim` via `shutil.copy2` mutated the open inode of the running `/bin/bash ./aim update` process, causing a syntax error when bash resumed reading at the old byte offset. Switched to atomic `os.replace(tmp_aim, dst_aim)`.
- Discovered and documented the legacy `aim-agy_os/` → `joshua_os/` migration pitfall: legacy `config_utils.py` (`find_project_root()`) walks up to `$HOME` if `~/aim-agy_os` exists unless the updated `config_utils.py` is copied into `joshua_os/.aim_core/` prior to invoking `./aim update`.
- Provisioned `/home/kingb/aim-skorbane` and upgraded all 16 active ecosystem and Co-Agent repositories (`aim-joshua`, `aim-skorbane`, `aim-calendar`, `aim-connect`, `aim-cron-dashboard`, `aim-ld`, `aim-tbsoftwash`, `aim-tmux-dashboard`, `aim-ayrianna`, `aim-youtube`, `aim-flight-recorder`, `aim-auditor`, `aim-gbp`, `aim-permits`, `aim-tbsoftwash-blogger`, and `aim-tester`) to `v0.7.3` with `./aim doctor` passing across the entire fleet.
- Updated `pages/operations.md` and `pages/handoff-and-retrieval.md`.

## [2026-10-20] ingest | Windows 10/11 Launchers, Pure-Python Push, MCP Cartridge Root & Ecosystem Lore Sync (`v0.8.0`, #98–#100)
- Added native Windows 10/11 root launchers (`aim.ps1` and `aim.cmd`) alongside `./aim`, cross-platform venv Python resolution (`resolve_venv_python()` in `config_utils.py` checking `Scripts/python.exe` and `bin/python3`), and Windows drive-root loop termination (`parent == current`) in `find_project_root()` (#98).
- Replaced the external `bash aim_push.sh` subprocess in `cmd_push` (`aim_cli.py`) with pure-Python `git_push_changes()`, adding an automatic `[NOTICE]` warning on `stderr` when untracked files are skipped by `git add -u` and an opt-in `--include-untracked` (`-a`) flag (#98).
- Normalized backslash paths in `cmd_promote` (`os.path.abspath(os.getcwd()).replace("\\", "/")`) and updated `cmd_update` and `ensure_consumer_gitignore` to atomically propagate and ignore `aim.ps1` and `aim.cmd` in consumer repos (#98).
- Added `get_active_aim_root()` in `retriever.py` so `archive/cartridges` and `archive/flashrank_cache` dynamically track `lance_backend.LANCE_DB_PATH` during MCP Local-First and Umbrella Subfolder queries (#99).
- Set default `github_projects` (`owner: BrianV1981`, `number: 7`, `status_field: Status`) in `config_utils.py`, bumped `VERSION` to `0.8.0`, and expanded the `pytest` suite to `32/32` passing tests.
- Authored two architectural essays in `/home/kingb/aim-knowledge/Philosophy_and_Concepts/` (*The Great Convergence: From Vessel Fragmentation to J.O.S.H.U.A.* and *J.O.S.H.U.A. vs. The Open-Source Harness Era*) and updated `AIM_ECOSYSTEM_HISTORY.md` (commit `c6b4d63`) documenting the Operator's origin story (`A.I.M.` named after Ayrianna, Isabella, and Michael; `J.O.S.H.U.A.` born from the `aim-ld-joshua` B2B field-sales pivot; and the X.com origin of the Forensic Blackbox Vault).
- Updated `pages/architecture.md`, `pages/operations.md`, `pages/projects.md`, and `pages/handoff-and-retrieval.md` (#100).

## [2026-10-21] ingest | Decouple Agent Memory (`memory-wiki/**` & `HANDOFF.md`) from Worktree GitOps (`v0.8.1`, #101)
- Decoupled Agent Memory state (`memory-wiki/**` and `HANDOFF.md`) from application code worktree GitOps in `AGENTS.md` (§6, §8, §9), `joshua_os/joshua_os_docs/PERSISTENT_WIKI.md`, and `joshua_os/joshua_os_docs/HANDOFF_PROTOCOL.md`.
- Configured `/aim-memory-wiki` across `aim-skill-library` (`skills/` and `vessels/agy/skills/`, commit `08511ae`) as a fast (~15s), autonomous mid-session "Save Game" checkpoint that commits and pushes `memory-wiki/` directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero issues, zero worktrees, and zero confirmation prompts.
- Added Step 1 **Idempotent Auto-Wiki Delta Check** and single atomic direct-to-`main` push (`git add memory-wiki/ HANDOFF.md`) to `/aim-handoff` across all vessels (`skills/`, `agy`, `grok`, `codex`, `opencode`).
- Fixed `bootstrap_brain.py` (`foundation_targets`) to index `os.path.join(PROJECT_ROOT, "memory-wiki", "**", "*.md")` with file deduplication, and expanded `pytest` coverage to `33/33` passing tests.


