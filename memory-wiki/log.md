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
