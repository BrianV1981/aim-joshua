# Changelog — aim-joshua

## 0.2.0 — 2026-08-12

### Fixed & Changed
- **Engine Version Bump**: `joshua_os/VERSION` advanced to `v1.0.8`.
- **Lexical Fallback (Issue 38)**: Upgraded LanceDB integration to fail-fast on vector embedding errors and cleanly degrade to pure Tantivy exact-keyword search.
- **Argparse Alignment (Issue 39)**: Fixed `retriever.py` to correctly consume `--top-k` and `--context` flags during deep CLI invocations.
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
