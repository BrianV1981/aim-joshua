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
- Upgraded all 16 active ecosystem and Co-Agent repositories across `~/aim-*` and `~/aim-agents/*` to `v0.7.3` with `./aim doctor` passing across the entire fleet.
- Updated `pages/operations.md` and `pages/handoff-and-retrieval.md`.

## [2026-10-20] ingest | Windows 10/11 Launchers, Pure-Python Push, MCP Cartridge Root & Ecosystem Lore Sync (`v0.8.0`, #98–#100)
- Added native Windows 10/11 root launchers (`aim.ps1` and `aim.cmd`) alongside `./aim`, cross-platform venv Python resolution (`resolve_venv_python()` in `config_utils.py` checking `Scripts/python.exe` and `bin/python3`), and Windows drive-root loop termination (`parent == current`) in `find_project_root()` (#98).
- Replaced the external `bash aim_push.sh` subprocess in `cmd_push` (`aim_cli.py`) with pure-Python `git_push_changes()`, adding an automatic `[NOTICE]` warning on `stderr` when untracked files are skipped by `git add -u` and an opt-in `--include-untracked` (`-a`) flag (#98).
- Normalized backslash paths in `cmd_promote` (`os.path.abspath(os.getcwd()).replace("\\", "/")`) and updated `cmd_update` and `ensure_consumer_gitignore` to atomically propagate and ignore `aim.ps1` and `aim.cmd` in consumer repos (#98).
- Added `get_active_aim_root()` in `retriever.py` so `archive/cartridges` and `archive/flashrank_cache` dynamically track `lance_backend.LANCE_DB_PATH` during MCP Local-First and Umbrella Subfolder queries (#99).
- Set default `github_projects` (`owner: BrianV1981`, `number: 7`, `status_field: Status`) in `config_utils.py`, bumped `VERSION` to `0.8.0`, and expanded the `pytest` suite to `32/32` passing tests.
- Authored two architectural essays in `~/aim-knowledge/Philosophy_and_Concepts/` (*The Great Convergence: From Vessel Fragmentation to J.O.S.H.U.A.* and *J.O.S.H.U.A. vs. The Open-Source Harness Era*) and updated `AIM_ECOSYSTEM_HISTORY.md` (commit `c6b4d63`) documenting the Operator's origin story and the Forensic Blackbox Vault.
- Updated `pages/architecture.md`, `pages/operations.md`, `pages/projects.md`, and `pages/handoff-and-retrieval.md` (#100).

## [2026-10-21] ingest | Decouple Agent Memory (`memory-wiki/**` & `HANDOFF.md`) from Worktree GitOps (`v0.8.1`–`v0.8.2`, #101–#102)
- Decoupled Agent Memory state (`memory-wiki/**` and `HANDOFF.md`) from application code worktree GitOps in `AGENTS.md` (§6, §8, §9), `joshua_os/joshua_os_docs/PERSISTENT_WIKI.md`, and `joshua_os/joshua_os_docs/HANDOFF_PROTOCOL.md` (#101).
- Configured `/aim-memory-wiki` across `aim-skill-library` (`skills/` and `vessels/agy/skills/`, commit `08511ae`) as a fast (~15s), autonomous mid-session "Save Game" checkpoint that commits and pushes `memory-wiki/` directly to `origin/main` (`git add memory-wiki/` + `git pull --rebase --autostash origin main` + `git push origin main`) with zero issues, zero worktrees, and zero confirmation prompts.
- Added Step 1 **Idempotent Auto-Wiki Delta Check** and single atomic direct-to-`main` push (`git add memory-wiki/ HANDOFF.md`) to `/aim-handoff` across all vessels (`skills/`, `agy`, `grok`, `codex`, `opencode`).
- Fixed `bootstrap_brain.py` (`foundation_targets`) to index `os.path.join(PROJECT_ROOT, "memory-wiki", "**", "*.md")` with file deduplication, and expanded `pytest` coverage to `33/33` passing tests.
- Aligned all remaining repository and wiki documentation (`COGNITIVE_ARCHITECTURE.md`, `GAMEPLAN_SOP.md`, `GITOPS_DEPLOYMENT.md`, `AIM_CLI_TOOLS.md`, `AGENTS_AMENDMENT_PROTOCOL.md`, `README.md`, `CONTRIBUTING.md`, `pages/active-memory-protocol.md`, `pages/operations.md`, and `pages/architecture.md`) with the direct-to-`main` memory state exemption and `/aim-handoff` Auto-Wiki Delta architecture (`v0.8.2`, #102, commit `cc9d13c0`).
- Executed a 4-wave surgical modernization of 22 `AGENTS.md` files across the active ecosystem (`aim-joshua`, `aim-coagents` blueprints, and active `~/aim-*` / `~/aim-agents/*` specialists), removing the stray `~/AGENTS.md` stub, standardizing Operator Name (`Brian Vasquez (@BrianV1981)`), purging legacy `/reincarnate`/`_ingest/`/`aim-agy_os` directives, and preserving 100% of custom domain sections using `git commit --only` for zero working-tree interference.
- Resolved #103 (`v0.8.3`, commit `4f950fbd`): eliminated the 7-line `AGENTS.md` stub overwrite in `aim_init.py` (`provision_agents_md` + `joshua_os/.aim_core/templates/default_AGENTS.md`), aligned `BOOTSTRAP.md` with the `v0.8.3` `AGENTS.md` schema, added optional persona argument (`$1`) resolution from `aim-coagents` to `install-agent.sh`, standardized all 4 `install*.sh` scripts (`install.sh`, `install-agent.sh`, `install-clean.sh`, `install-core.sh`), and expanded `pytest` coverage to `34/34` passing tests.
- Resolved #104 (`v0.8.4`, commit `9a5b5cef` & `aim-coagents` commit `d5f52a6`): added the 3-option installation comparison table and Turn-1 / `./aim init` personalization guide to `README.md`, rebuilt `joshua_os/assets/default_lance/` from scratch in a single compact transaction (`364 KB`, `58` fragments containing `v0.8.4` `AGENTS.md` and `joshua_os_docs/`), fixed `VectorBackend.__init__` in `lance_backend.py` to dynamically evaluate `LANCE_DB_PATH` when `path=None`, deduplicated `install-clean.sh` to delegate to `install.sh`, and updated `aim-coagents` (`README.md`, `SKILL.md`, `personas/README.md`) to point to `aim-joshua/main/joshua_os/install-agent.sh`.

## [2026-10-22] ingest | Ollama Fast-Fail Timeout & Audit Artifact Indexing (#105)
- Resolved #105 (`4c39858c`, `35/35` `pytest` passing in `14.87s`): changed local Ollama (`127.0.0.1:11434`) `timeout=15` to `timeout=(0.5, 15)` in `forensic_utils.py` and added `os.path.join(PROJECT_ROOT, "artifacts", "AUDIT_*.md")` to `foundation_targets` in `bootstrap_brain.py`.

## [2026-10-24] ingest | Onboarding `.gitignore` Fix (#107) & Host Path / Branch Hygiene (#108, `v0.8.6`)
- Resolved #107 (`v0.8.5`, commit `2c5d4bc4`): fixed `f.read().splitlines()` on pre-existing `.gitignore` files in `aim_init.py` with regression coverage in `tests/test_cli.py`.
- Resolved #108 (`v0.8.6`, commit `71a0b086`): removed hardcoded host-path comments from `agy_workspace_trust.py` and `spawn_sandbox.py`, added `test_no_hardcoded_host_paths_in_engine_code` (`37/37` `pytest` passing), sanitized host paths and private client references in `HANDOFF.md` and `memory-wiki/` while preserving all architectural wiki pages and `joshua_os/assets/default_lance/`, and pruned stale remote branches on `origin`.

## [2026-10-28] ingest | Fleet Blackbox Restoration, `/aim-sessions` Project Notebook & Ephemeral Pipeline Cleanup (`#110`, `v0.8.7`)
- Resolved `aim-joshua` `#110` (`v0.8.7`, `2da8423a`, `39/39` Pytest passing):
  - Fixed `blackbox_vault.py` (`get_candidate_keys()` + `audit_vault()`) to try both OS `keyring` and `~/.aim/blackbox.key` (prioritizing `manifest.jsonl` `key_source`), restoring `100%` decryption across all encrypted `.enc` blobs (`0` failures).
  - Added `index_session_to_history()` and `sync_vault_to_history()` in `blackbox_vault.py` and upgraded `cmd_sessions` / `cmd_search_sessions` in `cli_memory.py` so every sealed session is automatically rendered to `joshua_os/archive/history/<date>_<sid>.md` and indexed into `joshua_os/archive/history.db` (`history` + `history_fts` FTS5 tables) with unlimited retention (`4,000+` sessions).
  - Fixed `tests/test_aplus.py::test_vault_hermetic_decrypt` to use `tmp_path` instead of `os.getcwd()`, and added `cleanup_ephemeral_agy_sessions()` (`--project ephemeral-internal`) in `reasoning_utils.py`.
- Upgraded active consumer repositories to `v0.8.7` and backfilled `joshua_os/archive/history.db` across the fleet.

## [2026-10-28] ingest | Spoken Summary (`🔊`) Mandate & Fleet Neural TTS Rollout (`#111`–`#112`, `v0.8.8`–`v0.8.9`)
- Resolved `aim-joshua` `#111` (`v0.8.8`, `65d2d4ad`) and `#112` (`v0.8.9`, `23e4f752`, `39/39` Pytest passing):
  - Codified and expanded the **Spoken Summary (`🔊`)** mandate under `## 1. IDENTITY & PRIMARY DIRECTIVE` in `AGENTS.md` and `joshua_os/.aim_core/templates/default_AGENTS.md` so every agent turn concludes with a `🔊 <spoken summary>` block in plain conversational English (1–2 sentences for routine status updates; 3–6+ sentences or multi-paragraph blocks when elaborating or explaining architecture) for start-to-prompt Neural TTS readback.
  - Rebuilt `joshua_os/assets/default_lance` (`60` fragments) with the `v0.8.9` `AGENTS.md` and added regression assertions in `tests/test_cli.py`.
- Upgraded active consumer repositories to `v0.8.9` and surgically updated the `Spoken Summary (🔊)` mandate in each repository's `AGENTS.md` (`git commit --only AGENTS.md`), preserving 100% of custom domain rules.
- Updated `pages/dhh-agentic-philosophy.md` to document the Spoken Summary (`🔊`) Mandate and Neural TTS integration.

## [2026-10-29] ingest | Fleet-Wide Rollout Checklist in `operations.md` (Anti-Feature-Creep Decision)
- Evaluated and rejected building a dedicated `./aim fleet` CLI / `~/.aim/fleet.json` parser as unnecessary feature creep, reaffirming the DHH Agentic Doctrine that heterogeneous Markdown surgery across projects and Co-Agents belongs to the LLM agent combined with single-repo `./aim update`.
- Codified the 4-step **Fleet-Wide Rollout Checklist** in `pages/operations.md` (dynamic `joshua_os/.aim_core` + `~/aim-coagents/blueprints/*/AGENTS.md` discovery, `./aim update --source ~/aim-joshua --skip-deps`, surgical `AGENTS.md` patching, and dirty-worktree-safe `git commit --only AGENTS.md` + dynamic `main`/`master`/`local-only` push).

## [2026-10-30] ingest | Pre-`v1.0.0` Hygiene: LanceDB `list_lance_tables()` Fix (`#114`), Branch Sweep & `26.03 GiB` Host Archive Dehydration (`#113`, `v0.8.10`)
- Resolved `aim-joshua` `#114` (`v0.8.10`, `b3bddb0b`, `40/40` Pytest passing with `0` warnings):
  - Added forward/backward-compatible `list_lance_tables(db)` in `lance_backend.py` (unwrapping modern LanceDB `ListTablesResponse.tables` while preserving iterable and legacy `table_names()` fallbacks) and wired it across `lance_backend.py`, `retriever.py`, and `joshua_os/handoff/embed_store.py`.
  - Pruned all `8` stale remote `archive-fix/*` / `fix/issue-*` branches on `origin` and `12` local `archive-fix/*` branches so only `main` (`origin/main`) remains.
- Resolved `aim-joshua` `#113` (Host Pre-J.O.S.H.U.A. Legacy Archive Dehydration):
  - Created and verified (`git bundle verify`) cold-vault `.git.bundle` archives and dirty-worktree tarballs across `18` retired pre-J.O.S.H.U.A. vessels and sandboxes inside `~/aim_legacy_archive/cold_vault_20261030/` (`MANIFEST.json`), including archiving and removing the redundant `~/aim-joshua.bak-rsync-seed` directory.
  - Verified identical SHA256 (`656110d31168f6cc…`) across all `3` copies of `longmemeval_s.engram` (`941.4 MB` each) and replaced the two duplicate copies with symlinks to `~/aim_legacy_archive/engrams/longmemeval_s.engram`.
  - Dehydrated `203` inactive `venv`/`node_modules`/cache directories across `24` retired vessel and OS sandbox folders, reclaiming **`26.03 GiB`** total (`df -h` free space increased from `385G` to `410G`) with zero source or `.git` loss.

## [2026-10-30] ingest | J.O.S.H.U.A. `v1.0.0` General Availability Release (`#115`)
- Shipped `aim-joshua` `#115` (`v1.0.0`, commit `480511b0`, `41/41` Pytest passing with `0` warnings):
  - Graduated `README.md` from `"Alpha, trenches-first."` to `"v1.0 — Production-tested, trenches-first."` and documented the Forensic Blackbox Vault & `/aim-sessions` FTS5 Project Notebook under Core Capabilities.
  - Bumped `VERSION` to `v1.0.0`, prepended the `## [v1.0.0] - 2026-10-30` General Availability milestone entry to `CHANGELOG.md`, and added `test_semver_ga_posture()` in `tests/test_cli.py` enforcing SemVer `major >= 1` and non-Alpha `README.md` posture.
  - Published the inaugural official GitHub Release (`v1.0.0 — J.O.S.H.U.A. General Availability`) on `BrianV1981/aim-joshua` organized around the 5 core capability pillars, 10-second Quickstart, standardized single `aim-ecosystem` pointer, and full `CHANGELOG.md` history.

## [2026-10-30] ingest | Entity Page Consolidation for `v1.0.0` GA, Release SOP & Testing Architecture
- Synchronized `index.md`, `pages/architecture.md`, `pages/operations.md`, `pages/ci-testing.md`, and `pages/handoff-and-retrieval.md` with `v1.0.0` General Availability state:
  - Updated `pages/architecture.md` to reflect the `60`-fragment `v1.0.0` `default_lance` snapshot, forward-compatible `list_lance_tables(db)` (`#114`), and `cmd_sessions` / `cmd_search_sessions` in `cli_memory.py` (`#110`).
  - Purged stale `aim_push.sh` references in `pages/ci-testing.md` in favor of pure-Python `git_push_changes()` (`#98`) and documented the `41/41` (`0` warnings) `v1.0.0` Pytest regression gates.
  - Added the **Semantic Versioning & Official GitHub Release SOP** (`cmd_push` prefix vs. curated `Release:` mechanics, green-CI tagging gate, 5-part release notes standard) and **Cold-Vault Host Archive Dehydration** protocol (`#113`) to `pages/operations.md`, and interlinked `/aim-sessions` FTS5 recall + `cleanup_ephemeral_agy_sessions()` in `pages/handoff-and-retrieval.md`.

## [2026-10-31] ingest | Strict OS Kernel Wiki Scope & Single `aim-ecosystem` Pointer
- Removed non-kernel sibling-repository pages (`pages/aim-office-cockpit.md` and `pages/google-oct1-people-first-content.md`) and client/sibling domain entries from `memory-wiki/` and `HANDOFF.md` so `aim-joshua/memory-wiki/` stays 100% scoped to the J.O.S.H.U.A. OS kernel (while each sibling repository maintains its own `memory-wiki/`).
- Standardized the `v1.0.0` GitHub Release Notes ecosystem section to the single `aim-ecosystem` directory link and registered `aim-office` in `aim-ecosystem/README.md`.

## [2026-11-01] ingest | `#113` Audit Delta Closeout (`27.15 GiB` Total Reclaimed) & Local `install-agent.sh` Provisioning Notes
- Closed `aim-auditor`'s `#113` dotfile/root-tarball audit delta: verified bundle parity and removed a `1.2 GB` hidden `.aim_temp_clone` directory, verified `tar -ztf` integrity and relocated a `121.6 MB` root backup tarball into `~/aim_legacy_archive/cold_vault_20261030/`, and updated `MANIFEST.json` (`27.15 GiB` total reclaimed).
- Documented local `install-agent.sh <blueprint>` Co-Agent scaffolding sequence (`./aim` wrapper copy, `git branch -m main`, dual-vessel `aim-skill-library` symlink install, and clean `joshua_os/memory_lance/*` re-index after customizing `AGENTS.md`) and dotfile/tarball sweep guidance in `pages/operations.md`.

## [2026-11-01] ingest | Universal Cross-Platform Installer, Multi-Harness MCP Registration & Windows 10/11 Parity (`#116`, `v1.1.0`)
- Shipped `aim-joshua` `#116` (`v1.1.0`, commit `2207caf4`, `46/46` Pytest passing with `0` warnings) and companion `aim-skill-library` `#21` (`c018f85`, `14/14` unittest passing):
  - Created pure-Python `joshua_os/.aim_core/bootstrap_install.py` (`clean`, `agent`, and `core` onboarding modes with `$HOME`/`/`/Windows drive-root guard, cross-platform `venv` builder, and PowerShell `$PROFILE` alias helper) plus thin native Windows 10/11 PowerShell shims (`install.ps1`, `install-agent.ps1`, `install-core.ps1`).
  - Rewrote `joshua_os/.aim_core/register_mcp.py` to bind `joshua_os/venv` Python + absolute `mcp_lancedb.py` across `agy` (`~/.gemini/config/mcp_config.json`), `grok` (`~/.grok/config.toml`), `codex` (`~/.codex/config.toml`), `opencode` (`~/.config/opencode/opencode.json`), and existing `cursor`/`claude` configs, with automatic self-healing when stale sandbox binaries are deleted.
  - Added `_uri_to_local_path()` (decoding Windows `file:///C:/...` & `%20` workspace URIs) and venv `sys.path` self-bootstrap to `mcp_lancedb.py`, gated `SecretStorage>=3.5.0; sys_platform == 'linux'` in `requirements.txt`, guarded `dpkg` / `sudo -n` in `setup.sh`, fixed Windows drive-root loop termination + missing-`tmux` fallback in `aim_init.py`, and wired `cmd_update` (`aim_cli.py`) to sync `install*.ps1` and rebuild venv dependencies cross-platform.
  - Added `scripts/install.py` (`--mode auto|symlink|copy` with `WinError 1314` copy fallback) and `scripts/install.ps1` to `aim-skill-library`, promoted the universal skill pack across `agy`, `grok`, `codex`, and `opencode`, documented the **Tier 1 Universal Core vs. Tier 2 POSIX Swarm** capability matrix in `README.md`, and deprecated/archived standalone `BrianV1981/agy-joshua` with a redirect to `aim-joshua`.
- Updated `index.md`, `pages/architecture.md`, `pages/operations.md`, and `pages/ci-testing.md`.

## [2026-11-01] ingest | Steward Cross-Link Audit for `v1.1.0` Tier 1/Tier 2 Parity
- Audited `c1ae7ad8` across all `memory-wiki/` pages following `aim-connect`'s `v1.1.0` cross-platform sync dispatch:
  - Updated `pages/handoff-and-retrieval.md` with Tier 2 POSIX scoping for `tmux` baton passes, multi-harness `register_mcp.py` registration, `_uri_to_local_path()` Windows `file:///C:/...` URI normalization, and cross-platform CLI search fallbacks (`./aim`, `.\aim.ps1`).
  - Cross-linked `pages/bwrap-forge-skill.md` and `pages/native-os-shift.md` with the `v1.1.0` Tier 1 Universal Core vs. Tier 2 POSIX Swarm boundary and `BrianV1981/agy-joshua` archival.
  - Aligned `pages/operations.md` `ensure_consumer_gitignore` and atomic `os.replace` bullets with `aim.ps1`/`aim.cmd` launchers and recorded `v1.1.0` `main` vs. `v1.0.0` GitHub Release tag status.

## [2026-11-02] ingest | Pass 10 Audit Remediation & J.O.S.H.U.A. `v1.1.1` Release (`#117`–`#126`)
- Remediated all 10 Pass 10 audit tickets (`#117`–`#126`, merged on `main` @ `84949726`, `51/51` Pytest passing with `0` warnings under `-W error::DeprecationWarning`) and cut official GitHub Release `v1.1.1`:
  - **Idempotent Batch RAG Indexing (`#122`):** Added `VectorBackend.upsert_fragments()` and `rebuild_fts_index()` (`FTS(with_position=True)` + legacy fallback) in `lance_backend.py` and collision-free repo-relative `compute_doc_session_id()` + `table.optimize(cleanup_older_than=timedelta(seconds=0))` in `bootstrap_brain.py`. Rebuilt `joshua_os/assets/default_lance` (`185` files -> `10` files, `372 KB`, `60` fragments) and compacted live `memory_lance` (`402` duplicate rows -> `138` unique rows, stable across consecutive `./aim index` runs).
  - **Windows PowerShell & Antigravity 2.0 Hardening (`#117`–`#120`, `#123`):** Replaced PS 5.1 `@("-3")` array splatting with literal `& py -3` + `$null |` stdin probe across `install*.ps1` (`#117`); added Rule 3 `_os_root/memory_lance` fallback and `AIM_WORKSPACE_ROOT` in `mcp_lancedb.py` for Antigravity 2.0 Desktop (`#118`); centralized `~/.gemini/antigravity` + `~/.gemini/antigravity-cli` resolvers in `config_utils.py` across vault, handoff, session recall, workspace trust, and hooks while enforcing `sys.exit(1)` on blackbox failures (`#119`); updated `README.md` Antigravity 2.0 global skills path to `~/.gemini/config/skills` (`#120`); and replaced bare `python3` fallback (`rc=9009` Windows Store stub), scoped `tmux` to POSIX in `AGENTS.md` + `default_AGENTS.md`, and hardened Windows OneDrive `Documents` + ASCII `$PROFILE` handling (`#123`).
  - **Session FTS5 Sanitization, Unified `VERSION` & POSIX Shim Parity (`#121`, `#124`–`#126`):** Added `_sanitize_fts5_query()` + `sys.exit(1)` error handling to `./aim search-sessions` (`#124`); enforced `git init -b main` across `bootstrap_install.py`, `setup_environments.sh`, and `spawn_sandbox.py` (`#121`); refactored `joshua_os/install.sh`, `install-agent.sh`, and `install-core.sh` into thin POSIX shims delegating to `bootstrap_install.py` (`#126`); and unified root `VERSION` + `joshua_os/VERSION` (`v1.1.1`) alongside `BOOTSTRAP.md` sync in `cmd_update` (`#125`).
- Updated `index.md`, `pages/architecture.md`, `pages/operations.md`, `pages/handoff-and-retrieval.md`, `pages/blackbox-vault.md`, and `pages/ci-testing.md`.

## [2026-11-02] ingest | Pass 12 Google EGM Cold-Reader Audit Remediation & J.O.S.H.U.A. `v1.1.2` Release (`#127`–`#135`)
- Remediated all 9 Pass 12 Google Elephant-Goldfish Model (`egm@0.1.0`) audit tickets (`#127`–`#135`, merged on `main` @ `f26e4e3c`, `62/62` Pytest passing on both `ubuntu-latest` and `windows-latest` with `0` warnings under `-W error::DeprecationWarning`) and cut official GitHub Release `v1.1.2`:
  - **Host-Safe Uninstall/Purge & Clean Launcher Exit (`#127`):** Rewrote `cmd_uninstall` (`--yes`, `--purge-memory`) and `cmd_purge` (`--yes`) in `cli_memory.py` to remove strictly J.O.S.H.U.A.-owned files without ever touching host `.git/`, `src/`, `venv/`, `requirements.txt`, or `LICENSE`, and deleted the caller-`$PWD` git teardown block from `aim`, `aim.ps1`, `aim.cmd`, and `link_cli_alias.sh` (preserving `--json` stdout purity).
  - **Cross-Platform Root Guards, Non-Destructive Configs & Dual-OS CI (`#128`, `#129`):** Replaced all POSIX-only `!= '/'` root loops with `Path.parents`, guarded `fcntl`/`select` on `os.name != 'nt'`, added `cryptography>=42.0.0` to `requirements.txt`, removed `"Escape"` before `"Enter"` in `aim_init.py`, preserved third-party hooks and JSONC files in `aim_init.py` / `register_mcp.py` / `agy_workspace_trust.py`, unified `AIM_ROOT = OS_ROOT` + relocation-only atomic `CONFIG.json` writes in `config_utils.py` (`0` `[PORTABILITY]` spam), auto-detected `github_projects.owner` from `remote.origin.url`, and added a `windows-latest` matrix leg to `.github/workflows/smoke-test.yml`.
  - **LanceDB Concurrency, SQL Quoting & Cached Offline Vectors (`#130`):** Added thread-reentrant cross-platform `.lance.lock` write serialization (`fcntl`/`msvcrt`), `sql_quote()` across all DataFusion `.where(...)`/`.delete(...)` predicates, `timedelta(minutes=5)` live compaction retention, explicit `db_path=` plumbing in `mcp_lancedb.py` + `retriever.py` (zero global `LANCE_DB_PATH` mutation), SHA-256 cached 768-dim vector preservation when Ollama is offline, and removed dead `flashrank` code.
  - **Blackbox Security, Zombie Purge, Clean-Worktree Promote & Zip-Slip Defense (`#131`–`#135`):** Scoped `cmd_opencode_blackbox` strictly by `session_id` (`rc=1` on empty match), added `0600` `tempfile.mkstemp` cleanup, `PRAGMA journal_mode=WAL; busy_timeout=5000` on `history.db`, and shrink-overwrite protection + `snapshots/` rotation (`#132`); removed 28 zombie/legacy scripts and stale docs, repaired `handoff/cli.py` `e2e-staged` + `plugins/datajack/aim_exchange.py`, enforced `build_parser() == COMMAND_HANDLERS` parity (`#133`, `#134`); added clean-worktree/local-only `cmd_promote` guards and release-pinned `safe_extract_zip()` Zip-Slip/symlink validation in `cmd_update` (`#135`); and reconciled all docs + re-baked `default_lance` (`56` fragments, `#131`).
- Updated `index.md`, `pages/architecture.md`, `pages/operations.md`, `pages/blackbox-vault.md`, and `pages/ci-testing.md`.

## [2026-11-02] ingest | Pass 13 Audit Delta Remediation & J.O.S.H.U.A. `v1.1.3` Release (`#132`, `#134`, `#135`)
- Remediated all 3 reopened Pass 13 audit delta tickets (`#132`, `#134`, `#135`, promoted to `main` @ `55982475`, `66/66` Pytest passing on both `ubuntu-latest` and `windows-latest` with `0` warnings under `-W error::DeprecationWarning`) and cut official GitHub Release `v1.1.3`:
  - **Unmocked `./aim health` & `./aim clean` + Fail-Closed DB Diagnostics (`#134`):** Fixed `VectorBackend(path=lance_dir)` in `heartbeat.py`, returned `True` from `VectorBackend.compact()` in `lance_backend.py`, wired `--immediate` and optional `[days]` retention flags through `./aim clean`, propagated `rc=1` from `./aim audit` and `./aim recall` (`audit_tools.py` / `recall_tools.py` / `cli_memory.py`) when `history.db` is missing or corrupt, replaced `os.system('clear')` in `aim_config.py` with cross-platform `_clear_screen()`, and added live unmocked `health` + `clean` steps to both Linux and Windows legs of `.github/workflows/smoke-test.yml`.
  - **Out-of-the-Box Day-0 & Existing-Repo Local-Only `fix -> promote` (`#135`):** Updated `bootstrap_install.py` (`_create_initial_scaffold_commit`) to commit the initial baseline scaffold on `main` when initializing a brand-new `.git` directory (`not had_git`, with committer identity fallback and `commit.gpgsign=false`) while leaving pre-existing repositories untouched; added an unborn-`HEAD` guard (`git rev-parse --verify HEAD`) to `cmd_fix` so manual 0-commit repos exit `rc=1` with actionable guidance instead of creating `--orphan` worktrees; changed `cmd_promote` Safety Gate 2 to `git status --porcelain -uno` on `repo_root` so untracked scaffold/user files never block promotion while modified/staged tracked root files still abort (`rc=1`); handled Windows parent-shell working-directory locks during `cmd_promote` worktree removal and batch self-unwinding (`(goto) 2>nul & ...`) in `aim.cmd` during `uninstall`; removed `0`-byte `CHANGELOG.md`, `CONTRIBUTING.md`, and `VERSION` stubs from `aim_init.py`; and pruned empty `workspace/` directories in `cmd_uninstall`.
  - **Cross-Directory `--vessel-root` Blackbox Isolation (`#132`):** Wired `_resolve_vessel_root(args)` (`--vessel-root` / `--vessel`) across `cmd_vault`, `cmd_agy_blackbox`, `cmd_grok_blackbox`, `cmd_codex_blackbox`, `_resolve_opencode_db()`, and `cmd_opencode_blackbox` in `cli_vault.py`, verified by real unmocked cross-directory subprocess E2E tests in `tests/test_v1_1_3_remediation.py`.
- Updated `index.md`, `pages/architecture.md`, `pages/operations.md`, `pages/blackbox-vault.md`, and `pages/ci-testing.md`.

## [2026-11-02] ingest | Two-Pass `v1.1.3` Consumer Fleet Rollout Across `21/21` Active Workspaces (Pass 14 `A+` Certified)
- Following `aim-auditor` Pass 14 `A+` certification (`9/9` EGM findings `#127`–`#135` closed), upgraded all `21` active downstream consumer workspaces (`10` Co-Agent desks + `11` product/tooling workspaces) from `v0.8.2` to `v1.1.3`:
  - **Two-Pass Bootstrap Lesson (`v0.8.2 -> v1.1.3`):** Executed `./aim update --source ~/aim-joshua --skip-deps` twice per workspace (Pass 1 swapped `.aim_core/` to `v1.1.3`; Pass 2 executed `v1.1.3`'s `cmd_update` to sync `assets/default_lance`, `foundry/`, `BOOTSTRAP.md`, `install*.sh`, `install*.ps1`, `aim.ps1`, `aim.cmd`, `ensure_consumer_gitignore()`, and prune retired `DAEMON_PULSE.md` / `default_engrams`).
  - **Reader-Safe LanceDB Deduplication & Verification (`21/21` Green):** Ran `./aim index` (avoiding `clean --immediate` while live `mcp_lancedb.py` readers were attached), eliminating legacy `v0.8.2` duplicate/basename-colliding rows across the fleet while verifying `joshua_os/VERSION == v1.1.3`, 2x `./aim doctor` (`rc=0`, `0` `[PORTABILITY]`, `CONFIG.json` `st_mtime_ns` invariant), `./aim health` (`rc=0`), byte-for-byte `AGENTS.md`/`HANDOFF.md` SHA-256 invariance, and zero git mutations across all `21` consumer workspaces.

