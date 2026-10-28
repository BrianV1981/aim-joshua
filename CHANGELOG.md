# Changelog

## [v0.8.8] - 2026-10-28
- Fix: codify Spoken Summary (🔊) mandate in AGENTS.md and default_AGENTS.md (Closes #111)


## [v0.8.7] - 2026-10-28
- Fix: multi-key blackbox decrypt, auto-index handoffs to history.db, and ./aim sessions notebook (Closes #110)


## [v0.8.6] - 2026-10-24
- Fix: remove hardcoded /home/kingb comments and add host-path regression test (Closes #108)


## [v0.8.5] - 2026-10-23
- Fix: aim_init.py f.read().splitlines() on existing .gitignore (Closes #107)


## [v0.8.2] - 2026-10-21
- Fix: align joshua_os_docs, README.md, CONTRIBUTING.md, and memory-wiki pages with direct-to-main memory state (Closes #102)


## [v0.8.1] - 2026-10-21
- Fix: decouple memory-wiki and HANDOFF.md from worktree GitOps (Closes #101)


## [v0.8.0] - 2026-10-20
- Feature: Add Windows 10/11 launchers, pure-Python git_push_changes, and dynamic MCP cartridge root (Closes #98, Closes #99)


## [v0.7.4] - 2026-10-20
- Fix: Ingest consumer .gitignore safeguards, atomic ./aim updates, and 16-repo fleet upgrade into memory-wiki (Closes #97)


## [v0.7.3] - 2026-10-20
- Fix: Use atomic os.replace when updating ./aim wrapper in cmd_update (Refs #96)


## [v0.7.2] - 2026-10-20
- Fix: Auto-populate consumer .gitignore with joshua_os/, aim, workspace/, and archive/ (Closes #96)


## [v0.7.1] - 2026-10-20
- Fix: Harden install.sh and clarify README.md project onboarding & customization flow (Closes #95)


## [v0.7.0] - 2026-10-20
- Feature: Add automatic local-first + umbrella subfolder fallback to mcp_lancedb.py (Closes #94)


## [v0.6.0] - 2026-10-19
- Feature: Modularize aim_cli.py, fix legacy relative imports, and expand pytest suite for A+ bar (Closes #93)


## [v0.5.0] - 2026-10-19
- Feature: Harden aim update for Co-Agent fleet engine rollouts (Closes #92)


## [v0.4.3] - 2026-10-19
- Fix: Standardize README.md ecosystem section to AIM_ECOSYSTEM block (Closes #90)


## [v0.4.2] - 2026-10-19
- Fix: Remove deprecated swarm CLI routes and parser from aim_cli.py (Closes #89)


## [v0.4.1] - 2026-10-19
- Fix: Reconcile local Git and worktree drift (Closes #87)


## [v0.4.0] - 2026-08-28
- Feature: Implement Agentic Era Protocols from DHH Insights (Closes #84)


## [v0.3.4] - 2026-08-28
- Fix: CLI router swallows aim index arguments & Update Docs (Closes #82)


## [v0.3.3] - 2026-08-27
- Fix: Implement tests for MCP server and fix ingestion engine blindspot (Closes #81)


## [v0.3.2] - 2026-08-27
- Fix: Wiki: Update architecture.md for MCP Two-Tier Protocol (Closes #80)


## [v0.3.1] - 2026-08-27
- Fix: Docs: Update AGENTS.md for Two-Tier Retrieval Protocol (MCP + Fallback) (Closes #79)


## [v0.3.0] - 2026-08-26
- Feature: Architectural Upgrade: Migrate LanceDB Search to MCP Server (Closes #78)


## [v0.2.9] - 2026-08-12
- Fix: `--json` search keeps NOTICE on stderr so GHA can parse JSON (Closes #72)
- Fix: Hermetic `./aim vault seal --path` + `audit` test (no `~/.gemini` layout)
- Docs: Honest HANDOFF (no A+ self-award); collapse duplicate v0.2.8 headings

## [v0.2.8] - 2026-08-12
- Feature: Extended pytest via `./aim` for search, JSON, vault doctor, promote math (Closes #69, #71)
- Fix: Map footer `./aim search` (Closes #70)

## [v0.2.7] - 2026-08-12
- Fix: JOSH-022 and JOSH-023 HANDOFF and CHANGELOG (Closes #68)


## [v0.2.6] - 2026-08-12
- Fix: JOSH-021 Case-fold doctor assert and source venv in GHA (Closes #67)


## [v0.2.5] - 2026-08-12
- Feature: Added Pytest framework (#63), built E2E aim promote integration test (#64), and added Gitleaks secrets scanner CI (#65)
- Fix: Add CHANGELOG 0.2.1 and remove stale --context claim (Closes #62)


## [0.2.4] - 2026-08-12
- Fix: Remove deleted wiki_tools import from session_summarizer.py (Closes #61)

## [0.2.3] - 2026-08-12
- Fix: Change SOURCE.md Runtime from AGY to CLI-agnostic (Closes #60)

## [0.2.2] - 2026-08-12
- Fix: Wire doctor under aim vault (Closes #59)

## [0.2.1] - 2026-08-12
- Fix: Dynamic default branch in aim_batch_merge.py (Closes #57)

## 0.2.0 — 2026-08-12

### Fixed & Changed
- **Engine Version Bump**: `joshua_os/VERSION` advanced to `v1.0.8`.
- **Lexical Fallback (Issue 38)**: Upgraded LanceDB integration to fail-fast on vector embedding errors and cleanly degrade to pure Tantivy exact-keyword search.
- **Argparse Alignment (Issue 39)**: Fixed `retriever.py` to correctly consume `--top-k` flags during deep CLI invocations.
- **GitOps Promote (Issue 37)**: Fixed a catastrophic path resolution bug in `cmd_promote` by leveraging `git rev-parse --git-common-dir` instead of hardcoded directory traversal. Added runtime `.git` safety assertion.
- **Architectural Cleanup (Issue 40)**: Deprecated and deleted the obsolete `wiki_tools.py` SQLite engine. All wiki knowledge retrieval is now correctly routed through the unified `aim search` LanceDB engine.
- **Repo Hygiene & Licensing (Issue 41)**: Added standard MIT License. Revamped `.gitignore`. Fully untracked raw `memory_lance` objects and bloated `__pycache__` artifacts from git history.
- **CI/CD Pipeline (Issue 42)**: Implemented automated GitHub Action smoke tests (`.github/workflows/smoke-test.yml`) to ensure environment integrity and verify `./aim --help` compiles natively on pushed code.
- **Knowledge Re-index (Issue 44)**: Completely re-baked and synchronized the LanceDB `memory_lance` database to ingest the current documentation state.

## 0.1.0 — 2026-07-24

### Added

- Specialized vessel seeded from `aim-opencode` (no venv, engrams, secrets, or git history).
- LeadDeed product `README.md` and J.O.S.H.U.A. `AGENTS.md`.
- `SOURCE.md` pin (vessel base + soul lineage) and `VESSEL.md` spawn card.
- Fresh `memory-wiki/` bootstrap for product lore.
- GitHub repo `BrianV1981/aim-joshua` (private product vessel) with optional `upstream` → aim-opencode.
