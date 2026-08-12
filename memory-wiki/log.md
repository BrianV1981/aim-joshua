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
