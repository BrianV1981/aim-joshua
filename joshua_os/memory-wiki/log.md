# Memory Log
An append-only chronological log of session insights committed to the wiki using the `aim-memory-wiki` skill.

## [2026-07-26] ingest | Shift to Active Memory Protocol
- Purged 1,600+ lines of background ingestion daemons and cron logic.
- Purged 27 garbage Pytest artifact pages from the old background vacuum.
- Scaffolded fresh wiki and activated the strictly-interactive `aim-memory-wiki` skill pipeline.

## [2026-08-10] ingest | Native OS Shift & GitOps Worktree Enforcement
- Updated documentation and scripts to demote mandatory sandboxing to an optional feature.
- Refactored `aim` entrypoint teardown hook to support generalized Git repositories (e.g. worktrees) instead of hardcoded sandbox paths.
- Updated `AGENTS.md` to strictly enforce the `git worktree` protocol (`aim fix`, `aim promote`) for isolated parallel execution.
- Extracted bwrap sandbox orchestration into a dynamic skill (`aim-bwrap-forge`).
- Generalized Operator Name prompt in `AGENTS.md` for public OSS deployment.
- Created issues #16 and #17 to track `_ingest/` pipeline refactor and `joshua_os_docs/` documentation overhaul.
