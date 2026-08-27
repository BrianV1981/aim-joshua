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
